__all__ = [
    'Updater',
    'get_executable_path'
]

import time

import Version
import requests
from CliUi import Utils
from Updater import Errors
import os
import subprocess
from progress.bar import IncrementalBar
import sys
import __main__
import shutil


def get_executable_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    elif __file__:
        return os.path.abspath(__main__.__file__)
    else:
        return None


class Updater:
    latest_release_link = 'https://api.github.com/repos/LuTiFlekSSer/Spotify-downloader/releases/latest'

    def __init__(self):
        self._curr_version = Version.__version__
        self._latest_release_exe = None
        self._release_name = None

    def need_app_update(self):
        try:
            request = requests.get(self.latest_release_link)

            if request.status_code == 200 and not (request := request.json())['prerelease'] and not request['draft']:
                latest_release = request['tag_name']

                if Utils.compare_versions(self._curr_version, latest_release):
                    self._latest_release_exe = request['assets'][0]['browser_download_url']
                    self._release_name = request['assets'][0]['name']

                    return True

        except Exception:
            raise Errors.UpdateCheckError

        return False

    def download_update(self):
        if self._latest_release_exe is None:
            raise Errors.UpdateError

        request = requests.get(self._latest_release_exe, stream=True)

        total_size = int(request.headers.get('content-length', 0)) / 1024

        bar = IncrementalBar(Utils.Colors.END + 'Загрузка обновления', max=total_size, suffix='%(percent)d%% [%(elapsed_td)s / %(eta_td)s]')
        bar.start()

        with open(os.getenv('TEMP') + f'\\{self._release_name}', 'wb') as file:
            for data in request.iter_content(chunk_size=1024):
                bar.next()
                file.write(data)

        bar.finish()

    def start_update(self):
        if (path := get_executable_path()) is None:
            print(Utils.red('Не удалось получить путь до текущего файла'))

            time.sleep(2)

            return
        elif path.endswith('.py'):
            path = path[:-3] + '.exe'

        subprocess.Popen(f'{os.getenv("TEMP")}\\{self._release_name} -U "{path}"',
                         creationflags=subprocess.CREATE_NEW_CONSOLE)

    def install_update(self, path_to_exe):
        attempts = 0

        while attempts < 3:
            try:
                shutil.copy(get_executable_path(), path_to_exe)
                break
            except Exception:
                time.sleep(2)

            attempts += 1

        if attempts == 3:
            raise Errors.UpdateError
