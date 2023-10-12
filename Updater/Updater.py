__all__ = [
    'Updater'
]

import Version
import requests
from CliUi import Utils
import Errors
import os


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
                latest_release = request.json()['tag_name']

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

        request = requests.get(self._latest_release_exe).content

        with open(os.getenv('TEMP') + f'\\{self._release_name}', 'wb') as file:
            file.write(request)

    def install_update(self):
        os.system(f'{os.getenv("TEMP")}\\{self._release_name} -U -pid {os.getgid()}')
