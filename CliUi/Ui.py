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
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import win32com.client
import time


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
        os.system('cls')
        print(f'Смена кол-ва потоков для загрузки треков\n\nТекущее кол-во: {self._settings.get_setting("threads")}')

        while True:
            threads = input('Введи кол-во потоков (0 - для отмены)\n> ')

            if not threads.isnumeric():
                print('Ошибка ввода')
                continue

            if threads == '0':
                print('Отменено')
                time.sleep(1)
                break

            self._settings.change_setting('threads', threads)
            print(f'Кол-во потоков изменено на {threads}')
            time.sleep(1)
            break

    def _settings_set_path(self):
        os.system('cls')
        print(f'Смена папки, в которой производится синхронизация треков\n\nТекущее расположение: {"Не задано" if (directory := self._settings.get_setting("path_for_sync")) == "" else directory}')

        print('[1] - Поменять расположение\n'
              '[2] - Отмена')

        while True:
            match input('> '):
                case '1':
                    try:
                        directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                        self._settings.change_setting('path_for_sync', directory)

                        print(f'Кол-во потоков изменено на {directory}')
                        time.sleep(1)

                    except Exception:
                        print('Отменено')
                        time.sleep(1)

                    break

                case '2':
                    print('Отменено')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')

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
