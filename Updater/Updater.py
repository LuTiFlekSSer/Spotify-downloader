__all__ = [
    'Updater',
]

import time

import Version
import requests
from Ui import Utils
from Updater import Errors
import os
import subprocess
import shutil


class Updater:
    latest_release_link = 'https://api.github.com/repos/LuTiFlekSSer/Spotify-downloader/releases/latest'

    def __init__(self):
        self._total_size = None
        self._curr_version = Version.__version__
        self._latest_release_exe = None
        self._release_name = None
        self._request = None

    def need_app_update(self):
        try:
            request = requests.get(self.latest_release_link)

            if request.status_code == 200 and not (request := request.json())['prerelease'] and not request['draft']:
                latest_release = request['tag_name']

                try:
                    if Utils.compare_versions(self._curr_version, latest_release):
                        self._latest_release_exe = request['assets'][0]['browser_download_url']
                        self._release_name = request['assets'][0]['name']

                        return True
                except ValueError:
                    raise Errors.UpdateCheckError

        except Exception:
            raise Errors.UpdateCheckError

        return False

    def get_total_size(self):
        if self._total_size is None:
            raise Errors.UpdateError

        return self._total_size

    def start_download(self):
        if self._latest_release_exe is None:
            raise Errors.UpdateError

        try:
            self._request = requests.get(self._latest_release_exe, stream=True)
        except Exception:
            raise Errors.UpdateError

        self._total_size = int(self._request.headers.get('content-length', 0)) / 1024

    def download_update(self):
        if self._latest_release_exe is None or self._request is None:
            raise Errors.UpdateError

        with open(os.getenv('TEMP') + f'\\{self._release_name}', 'wb') as file:
            for i, data in enumerate(self._request.iter_content(chunk_size=1024)):
                file.write(data)

                yield i

    def start_update(self):
        if (path := Utils.get_executable_path()) is None:
            raise Errors.UpdateError

        elif path.endswith('.py'):
            path = path[:-3] + '.exe'

        try:
            subprocess.Popen(
                f'{os.getenv("TEMP")}\\{self._release_name} -U "{path}"',
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception:
            raise Errors.UpdateError

    @staticmethod
    def install_update(path_to_exe):
        attempts = 0

        while attempts < 3:
            try:
                shutil.copy(Utils.get_executable_path(), path_to_exe)
                break
            except Exception:
                time.sleep(2)

            attempts += 1

        if attempts == 3:
            raise Errors.UpdateError
