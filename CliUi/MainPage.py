import os
import TracksSyncing
import TracksCompare
import PlaylistDownload
import MultipleTracksDownload
import SetSettings


def _print_greeting():
    os.system('cls')
    print('----------------------------------')
    print('| ADSKAYA KOCHALKA WELCOMES YOU! |')
    print('---------------------------------')
    print('What do you want to do?\n\n'
          '[1] - Синхронизировать треки с аккаунтом\n'
          '[2] - Проверить отсутсвующие треки на сервере\n'
          '[3] - Скачать треки из плейлиста по ссылке\n'
          '[4] - Скачать отдельные треки по ссылке\n'
          '[5] - Настройки\n\n'
          '[x] - Выход\n', end='')


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
            match input('> '):
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
                case 'x':
                    print('ББ')
                    break
                case _:
                    print('Ошибка ввода')
