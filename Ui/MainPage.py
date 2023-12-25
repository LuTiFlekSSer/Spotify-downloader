import os
import time

import TracksSyncing
import TracksCompare
import PlaylistDownload
import MultipleTracksDownload
import Utils
import Version
import customtkinter as ctk
import Locales
from PIL import Image


def _print_greeting():
    os.system('cls')
    print(Utils.cyan('------------------------------------\n'
                     '| SPOTIFY DOWNLOADER WELCOMES YOU! |\n'
                     '------------------------------------'))
    print(f'Версия: {Version.__version__}\n')
    print(f'What do you want to do?\n\n'
          f'{Utils.blue("[1]")} - Синхронизировать треки с аккаунтом\n'
          f'{Utils.blue("[2]")} - Проверить отсутствующие треки на сервере\n'
          f'{Utils.blue("[3]")} - Скачать треки из плейлиста по ссылке\n'
          f'{Utils.blue("[4]")} - Скачать отдельные треки по ссылке\n'
          f'{Utils.blue("[5]")} - Настройки\n\n'
          f'{Utils.purple("[c]")} - Очистка ввода\n'
          f'{Utils.purple("[x]")} - Выход\n', end='')


class MainPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self._locales = Locales.Locales()

        self._tracks_syncing = TracksSyncing.TracksSyncing()
        self._tracks_compare = TracksCompare.TracksCompare()
        self._playlist_download = PlaylistDownload.PlaylistDownload()
        self._multiple_tracks_download = MultipleTracksDownload.MultipleTracksDownload()

        self._sync_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/sync.png')), size=(30, 30))
        self._check_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/check.png')), size=(30, 30))
        self._playlist_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/playlist.png')), size=(30, 30))
        self._multiple_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/track.png')), size=(30, 30))

        self._menu_frame = ctk.CTkFrame(self)
        self._sync_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('sync_tracks'),
            image=self._sync_image,
            compound='top',
            command=...,

        )
        self._tracks_check_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('check_tracks'),
            image=self._check_image,
            compound='top',
            command=...,

        )
        self._playlist_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('download_playlist'),
            image=self._playlist_image,
            compound='top',
            command=...,

        )
        self._multiple_tracks_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('download_tracks'),
            image=self._multiple_image,
            compound='top',
            command=...,

        )

        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self._menu_frame.grid(row=1, column=1)
        self._sync_button.grid(row=0, column=0, padx=10, pady=10)
        self._tracks_check_button.grid(row=0, column=1, padx=10, pady=10)
        self._playlist_button.grid(row=1, column=0, padx=10, pady=10)
        self._multiple_tracks_button.grid(row=1, column=1, padx=10, pady=10)

    def main_page(self):
        _print_greeting()
        while True:
            match Utils.g_input('> '):
                case '1':
                    self._tracks_syncing.tracks_syncing()
                    _print_greeting()
                case '2':
                    self._tracks_compare.tracks_compare()
                    _print_greeting()
                case '3':
                    self._playlist_download.playlist_download()
                    _print_greeting()
                case '4':
                    self._multiple_tracks_download.multiple_tracks_download()
                    _print_greeting()
                case 'c':
                    _print_greeting()
                case 'x':
                    os.system('cls')
                    print(Utils.green(r'   _____  ____   ____  _____  ______     ________''\n'
                                      r'  / ____|/ __ \ / __ \|  __ \|  _ \ \   / /  ____|''\n'
                                      r' | |  __| |  | | |  | | |  | | |_) \ \_/ /| |__''\n'
                                      r' | | |_ | |  | | |  | | |  | |  _ < \   / |  __|''\n'
                                      r' | |__| | |__| | |__| | |__| | |_) | | |  | |____''\n'
                                      r'  \_____|\____/ \____/|_____/|____/  |_|  |______|'))
                    time.sleep(1)
                    break
                case _:
                    print(Utils.red('Ошибка ввода'))
