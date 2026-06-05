import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import requests

from src.utils.config import Config
from src.utils.utils import compare_versions, get_executable_path, is_frozen
from src.version import __version__


@dataclass
class ReleaseInfo:
    version: str
    download_url: str
    name: str


class UpdateError(Exception):
    pass


class UpdateCheckError(Exception):
    pass


class Updater:
    """Самообновление приложения (Windows, frozen .exe).

    Поток: check() сравнивает версию с последним релизом GitHub; при наличии
    обновления — start_download()/download() качают новый .exe в %TEMP%, затем
    launch_installer() запускает его с `-U "<текущий exe>"` и приложение выходит.
    Новый .exe (через main.py: -U) копирует себя поверх старого пути и перезапускает.
    """

    _HEADERS = {
        'User-Agent': f'Spotify-Downloader/{__version__}',
        'Accept': 'application/vnd.github+json',
    }

    def __init__(self):
        self._current = __version__
        self._release: Optional[ReleaseInfo] = None
        self._request = None
        self._total = 0

    def check(self) -> Optional[ReleaseInfo]:
        """None — установлена последняя версия; ReleaseInfo — доступно обновление."""
        try:
            response = requests.get(Config.GITHUB_RELEASES_URL, headers=self._HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception:
            raise UpdateCheckError

        if data.get('prerelease') or data.get('draft'):
            return None

        tag = data.get('tag_name', '')
        try:
            newer = compare_versions(self._current, tag)
        except Exception:
            raise UpdateCheckError

        if not newer:
            return None

        assets = data.get('assets') or []
        exe = next((a for a in assets if a.get('name', '').lower().endswith('.exe')),
                   assets[0] if assets else None)
        if not exe:
            raise UpdateCheckError

        self._release = ReleaseInfo(tag, exe['browser_download_url'], exe['name'])
        return self._release

    @property
    def release(self) -> Optional[ReleaseInfo]:
        return self._release

    @staticmethod
    def is_frozen() -> bool:
        return is_frozen()

    def start_download(self):
        if self._release is None:
            raise UpdateError
        try:
            self._request = requests.get(self._release.download_url, stream=True,
                                         headers=self._HEADERS, timeout=30)
            self._request.raise_for_status()
        except Exception:
            raise UpdateError
        self._total = int(self._request.headers.get('content-length', 0))

    def download(self):
        """Генератор: пишет .exe в %TEMP% чанками, yield (скачано, всего) в байтах."""
        if self._release is None or self._request is None:
            raise UpdateError

        dest = os.path.join(os.getenv('TEMP', '.'), self._release.name)
        downloaded = 0
        try:
            with open(dest, 'wb') as file:
                for chunk in self._request.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        yield downloaded, self._total
        except Exception:
            raise UpdateError

    def launch_installer(self):
        """Запускает скачанный .exe с `-U <текущий путь>` для самоподмены."""
        if self._release is None:
            raise UpdateError
        target = get_executable_path()
        if target is None or target.endswith('.py'):
            raise UpdateError       # не frozen — самоподмена невозможна

        dest = os.path.join(os.getenv('TEMP', '.'), self._release.name)
        try:
            subprocess.Popen([dest, '-U', target], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception:
            raise UpdateError

    @staticmethod
    def install_update(target_path: str):
        """Вызывается новым .exe (main.py: -U): копирует себя поверх старого пути."""
        for _ in range(3):
            try:
                shutil.copy(get_executable_path(), target_path)
                return
            except Exception:
                time.sleep(2)
        raise UpdateError
