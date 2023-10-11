__all__ = [
    'Updater'
]

import Version
import requests
from CliUi import Utils
import Errors


class Updater:
    latest_release_link = 'https://api.github.com/repos/LuTiFlekSSer/Spotify-downloader/releases/latest'

    def __init__(self):
        self._curr_version = Version.__version__

    def need_app_update(self):
        try:
            request = requests.get(self.latest_release_link)

            if request.status_code == 200 and not (request := request.json())['prerelease'] and not request['draft']:
                latest_release = request.json()['tag_name']

                if Utils.compare_versions(self._curr_version, latest_release):
                    return True

        except Exception:
            raise Errors.UpdateCheckError

        return False
