import os
import TracksSyncing
import TracksCompare
import PlaylistDownload
import MultipleTracksDownload
import SetSettings
import Utils


def _print_greeting():
    os.system('cls')
    print(Utils.cyan('----------------------------------\n'
                     '| ADSKAYA KOCHALKA WELCOMES YOU! |\n'
                     '----------------------------------'))
    print(f'What do you want to do?\n\n'
          f'{Utils.blue("[1]")} - Синхронизировать треки с аккаунтом\n'
          f'{Utils.blue("[2]")} - Проверить отсутсвующие треки на сервере\n'
          f'{Utils.blue("[3]")} - Скачать треки из плейлиста по ссылке\n'
          f'{Utils.blue("[4]")} - Скачать отдельные треки по ссылке\n'
          f'{Utils.blue("[5]")} - Настройки\n\n'
          f'{Utils.purple("[c]")} - Очистка ввода\n'
          f'{Utils.purple("[x]")} - Выход\n', end='')


class MainPage:
    def __init__(self):
        self._tracks_syncing = TracksSyncing.TracksSyncing()
        self._tracks_compare = TracksCompare.TracksCompare()
        self._playlist_download = PlaylistDownload.PlaylistDownload()
        self._multiple_tracks_download = MultipleTracksDownload.MultipleTracksDownload()
        self._set_settings = SetSettings.SetSettings()

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
                case '5':
                    self._set_settings.set_settings()
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
                    break
                case _:
                    print(Utils.red('Ошибка ввода'))
