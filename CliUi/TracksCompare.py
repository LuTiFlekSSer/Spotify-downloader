import os
import SpotifyTracks
import TracksComparator
import SettingsStorage
import time
import SpLogin
import win32com.client
import LocalTracks


class TracksCompare:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._spotify_login = SpLogin.SpLogin()

    def tracks_compare(self):
        os.system('cls')
        print('Проверка отсутствующих треков на сервере\n')

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            print('Не задан путь к папке для синхронизации, задать сейчас? (y - да, n - нет)')

            while True:
                match input('> '):
                    case 'y':

                        try:
                            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                            self._settings.change_setting('path_for_sync', directory)

                            print(f'Путь изменен на: {directory}\n')

                            break
                        except Exception:
                            print('Проверка отменена')
                            time.sleep(1)

                            return
                    case 'n':
                        print('Проверка отменена')
                        time.sleep(1)
                        return
                    case _:
                        print('Ошибка ввода')

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

        spt = SpotifyTracks.SpTracks(spl)
        spt.start()
        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)

        server_missing_tracks = comp.get_server_missing_tracks()

        if len(server_missing_tracks) == 0:
            print('\nТреки на сервере синхронизированы\n')
        else:
            print('\nСписок отсутствующих треков на сервере:\n')
            for i, track in enumerate(server_missing_tracks):
                print(f'{i + 1}) {track}')
        print()
        print('[1] - Добавить треки в серверный игнор лист\n\n'
              '[b] - назад')

        while True:
            match input('> '):
                case '1':
                    name = input('Введи название трека\n> ')
                    try:
                        self._settings.add_track_to_server_ignore(name)
                        print(f'Трек "{name}" добавлен в игнор лист')
                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек "{name}" уже добавлен в игнор лист')
                case 'b':
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')
