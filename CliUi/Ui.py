__all__ = [
    'Cli'
]

import os


class Cli:
    def __init__(self):
        os.system('cls')
        print('-----------------------------------------')
        print('| ADSKAYA KOCHALKA v14.88 WELCOMES YOU! |')
        print('-----------------------------------------')
        print('What do you want to do?\n\n[1] - Синхронизировать треки с аккаунтом\n[2] - Скачать треки из плейлиста по ссылке\n[3] - Скачать отдельные треки по ссылке\n'
              '[4] - Настройки\n[5] - Выход\n> ', end='')

        while True:
            match input():
                case '1':
                    self._tracks_syncing()
                case '2':
                    self._playlist_download()
                case '3':
                    self._multiple_tracks_download()
                case '4':
                    self._settings()
                case '5':
                    break
                case _:
                    print('Ошибка ввода')

    def _tracks_syncing(self):
        pass

    def _playlist_download(self):
        pass

    def _multiple_tracks_download(self):
        pass

    def _settings(self):
        pass
