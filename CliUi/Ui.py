__all__ = [
    'Cli'
]

import os
import LocalTracks
import SettingsStorage
import SpotifyLogin
import SpotifyTracks
import TrackDownloader
import TracksComparator
from multiprocessing import Pool


def _print_greeting():
    os.system('cls')
    print('-----------------------------------------')
    print('| ADSKAYA KOCHALKA v14.88 WELCOMES YOU! |')
    print('-----------------------------------------')
    print('What do you want to do?\n\n[1] - Синхронизировать треки с аккаунтом\n'
          '[2] - Скачать треки из плейлиста по ссылке\n'
          '[3] - Скачать отдельные треки по ссылке\n'
          '[4] - Настройки\n[5] - Выход\n', end='')


def _print_settings():
    os.system('cls')
    print(f'Настройки\n\n[1] - Поменять кол-во потоков для загрузки треков\n'
          f'[2] - Поменять путь для синхронизации треков\n'
          f'[3] - Назад\n', end='')


class Cli:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

        self._main_page()

    def _main_page(self):
        _print_greeting()

        while True:
            match input('> '):
                case '1':
                    self._tracks_syncing()
                    _print_greeting()
                case '2':
                    self._playlist_download()
                    _print_greeting()
                case '3':
                    self._multiple_tracks_download()
                    _print_greeting()
                case '4':
                    self._set_settings()
                    _print_greeting()
                case '5':
                    print('ББ')
                    break
                case _:
                    print('Ошибка ввода')

    def _tracks_syncing(self):
        pass

    def _playlist_download(self):
        pass

    def _multiple_tracks_download(self):
        pass

    def _settings_set_threads(self):
        pass

    def _settings_set_path(self):
        pass

    def _set_settings(self):
        _print_settings()

        while True:
            match input('> '):
                case '1':
                    self._settings_set_threads()
                    _print_settings()
                case '2':
                    self._settings_set_path()
                    _print_settings()
                case '3':
                    break
                case _:
                    print('Ошибка ввода')
        pass
