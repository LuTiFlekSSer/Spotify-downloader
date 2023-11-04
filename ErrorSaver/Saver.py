__all__ = [
    'ErrorSaver'
]

import SettingsStorage
import os
import datetime
import traceback


class ErrorSaver:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

        self._directory = f'{os.getenv("APPDATA")}\\Spotify downloader\\Logs'

        if not os.path.exists(self._directory):
            os.mkdir(self._directory)

    def save_log(self):
        filename = datetime.datetime.now().isoformat().replace(':', '\ua4fd')
        path = f'{self._directory}\\{filename}.txt'

        with open(path, 'w+', encoding='UTF-8') as file:
            file.write(traceback.format_exc())

        return path
