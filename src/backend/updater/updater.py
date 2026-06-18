import os
import subprocess
from dataclasses import dataclass
from typing import Iterator, Optional

import requests

from src.utils.config import Config
from src.utils.utils import compare_versions, is_frozen
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
    обновления — start_download()/download() качают Inno-установщик в %TEMP%, затем
    launch_installer() запускает его в тихом режиме (/VERYSILENT /CLOSEAPPLICATIONS):
    установщик закрывает текущее приложение, обновляет файлы на месте (тот же AppId)
    и перезапускает приложение ([Run] в installer.iss без skipifsilent).
    """

    _HEADERS = {
        'User-Agent': f'Spotify-Downloader/{__version__}',
        'Accept': 'application/vnd.github+json',
    }

    def __init__(self) -> None:
        self._current = __version__
        self._release: Optional[ReleaseInfo] = None
        self._request: Optional[requests.Response] = None
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

        # выбираем именно Inno-установщик ("...Setup.exe"), а не любой .exe-ассет
        assets = data.get('assets') or []
        installer = next((a for a in assets if a.get('name', '').lower().endswith('.exe')
                          and 'setup' in a.get('name', '').lower()), None)
        if installer is None:
            installer = next((a for a in assets if a.get('name', '').lower().endswith('.exe')), None)
        if installer is None:
            raise UpdateCheckError

        self._release = ReleaseInfo(tag, installer['browser_download_url'], installer['name'])
        return self._release

    @property
    def release(self) -> Optional[ReleaseInfo]:
        return self._release

    @staticmethod
    def is_frozen() -> bool:
        return is_frozen()

    def start_download(self) -> None:
        if self._release is None:
            raise UpdateError
        try:
            self._request = requests.get(self._release.download_url, stream=True,
                                         headers=self._HEADERS, timeout=30)
            self._request.raise_for_status()
        except Exception:
            raise UpdateError
        self._total = int(self._request.headers.get('content-length', 0))

    def download(self) -> Iterator[tuple[int, int]]:
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

    def launch_installer(self) -> None:
        """Запускает скачанный Inno-установщик в тихом режиме. Он сам закрывает текущее
        приложение (/CLOSEAPPLICATIONS + AppMutex), обновляет файлы на месте (тот же
        AppId) и перезапускает приложение. Старый механизм самоподмены `-U` удалён —
        он не работал с standalone-сборкой (папка из ~270 файлов) и Inno-установщиком."""
        if self._release is None:
            raise UpdateError
        if not is_frozen():
            raise UpdateError       # из исходников самообновление не поддерживается

        dest = os.path.join(os.getenv('TEMP', '.'), self._release.name)
        if not os.path.isfile(dest):
            raise UpdateError
        try:
            subprocess.Popen(
                [dest, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                 '/CLOSEAPPLICATIONS', '/FORCECLOSEAPPLICATIONS', '/NOICONS'],
                creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception:
            raise UpdateError
