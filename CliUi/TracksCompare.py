import os
import SpotifyTracks
import TracksComparator
import SettingsStorage
import time
import SpLogin
import LocalTracks
import Utils


class TracksCompare:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._spotify_login = SpLogin.SpLogin()

    def tracks_compare(self):
        def print_menu():
            os.system('cls')
            print(Utils.cyan('Проверка отсутствующих треков на сервере\n'))

        print_menu()

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            if not Utils.set_sync_path(print_menu):
                return

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

        print_menu()

        spt = SpotifyTracks.SpTracks(spl)
        spt.start()
        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)

        server_missing_tracks = comp.get_server_missing_tracks()

        print_menu()

        def print_tracks():
            if len(server_missing_tracks) == 0:
                print(Utils.green('\nТреки на сервере синхронизированы\n'))
            else:
                print(Utils.yellow('\nСписок отсутствующих треков на сервере:\n'))

                for i, track in enumerate(server_missing_tracks):
                    print(f'{i + 1}) {track}')
                print()

            print(f'{Utils.blue("[1]")} - Добавить треки в серверный игнор лист\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - назад')

        print_tracks()

        while True:
            match Utils.g_input('> '):
                case '1':
                    res = Utils.add_tracks_to_ignore(server_missing_tracks, self._settings.add_track_to_server_ignore)

                    if res:
                        self._settings.save()

                        server_missing_tracks = comp.get_server_missing_tracks(refresh=True)

                        time.sleep(1)

                case 'c':
                    print_menu()
                    print_tracks()

                case 'b':
                    print(Utils.green('Возврат в меню'))
                    time.sleep(1)
                    break
                case _:
                    print(Utils.red('Ошибка ввода'))
