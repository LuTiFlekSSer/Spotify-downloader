import SettingsStorage
import os
import SpotifyTracks
import LocalTracks
import time
import TracksComparator
import SpLogin
import Utils


class TracksSyncing:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._spotify_login = SpLogin.SpLogin()

    def tracks_syncing(self):
        def print_menu():
            os.system('cls')
            print(Utils.cyan('Синхронизация треков с аккаунтом\n'))

        print_menu()

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            if not Utils.set_sync_path(print_menu):
                return

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

        print_menu()

        spt = SpotifyTracks.SpTracks(spl)
        try:
            spt.start()
        except SpotifyTracks.TracksGetError:
            print(Utils.red('Ошибка при получении треков из spotify'))
            time.sleep(1)
            return

        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)

        print_menu()

        if self._settings.get_setting('auto_comp') == 'True':
            server_missing_tracks = comp.get_server_missing_tracks()

            def print_server_menu():
                if len(server_missing_tracks) == 0:
                    print(Utils.green('\nТреки на сервере синхронизированы\n'))
                else:
                    print(Utils.yellow('\nСписок отсутствующих треков на сервере:\n'))
                    for i, track in enumerate(server_missing_tracks):
                        print(f'{i + 1}) {track}')
                    print()

                print(f'{Utils.blue("[1]")} - Продолжить синхронизацию треков\n'
                      f'{Utils.blue("[2]")} - Добавить треки в серверный игнор лист\n\n'
                      f'{Utils.purple("[c]")} - Очистка ввода\n'
                      f'{Utils.purple("[b]")} - Назад')

            print_server_menu()

            while True:
                match Utils.g_input('> '):
                    case '1':
                        break

                    case '2':
                        res = Utils.add_tracks_to_ignore(server_missing_tracks, self._settings.add_track_to_server_ignore)

                        if res:
                            server_missing_tracks = comp.get_server_missing_tracks(refresh=True)

                            time.sleep(1)

                            print_menu()
                            print_server_menu()

                    case 'c':
                        print_menu()
                        print_server_menu()

                    case 'b':
                        print(Utils.green('Возврат в меню'))
                        time.sleep(1)
                        return

                    case _:
                        print(Utils.red('Ошибка ввода'))

        local_missing_tracks = comp.get_local_missing_tracks()

        print_menu()

        if len(local_missing_tracks) == 0:
            def print_local_menu():
                print(Utils.green('\nЛокальные треки синхронизированы\n'))
                print(f'{Utils.purple("[c]")} - Очистка ввода\n'
                      f'{Utils.purple("[b]")} - Назад')

            print_local_menu()

            while True:
                match Utils.g_input('> '):
                    case 'c':
                        print_menu()
                        print_local_menu()

                    case 'b':
                        print(Utils.green('Возврат в меню'))
                        time.sleep(1)
                        return

                    case _:
                        print(Utils.red('Ошибка ввода'))

        def print_local_tracks():
            print(Utils.yellow('Список отсутствующих локальных треков:\n'))
            for i, track in enumerate(sorted(local_missing_tracks)):
                print(f'{i + 1}) {track}')

            print(f'\n{Utils.blue("[1]")} - Скачать отсутствующие треки\n'
                  f'{Utils.blue("[2]")} - Добавить треки в локальный игнор лист (новые треки будут сразу проигнорированы при загрузке)\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_local_tracks()

        while True:
            match Utils.g_input('> '):
                case '1':
                    break

                case '2':
                    res = Utils.add_tracks_to_ignore(sorted(local_missing_tracks), self._settings.add_track_to_local_ignore)

                    if res:
                        spt.refresh_track_list()

                        local_missing_tracks = comp.get_local_missing_tracks(refresh=True)

                        time.sleep(1)

                        print_menu()
                        print_local_tracks()

                case 'c':
                    print_menu()
                    print_local_tracks()

                case 'b':
                    print(Utils.green('Возврат в меню'))
                    time.sleep(1)
                    return

                case _:
                    print(Utils.red('Ошибка ввода'))

        Utils.start_playlist_download(Utils.cyan('Синхронизация треков с аккаунтом\n'),
                                      [(track, self._settings.get_setting('path_for_sync'), local_missing_tracks[track]) for track in local_missing_tracks])
