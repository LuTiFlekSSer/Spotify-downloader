import os
import SpotifyTracks
import TracksComparator
import SettingsStorage
import time
import SpLogin


class TracksCompare:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._spotify_login = SpLogin.SpLogin()

    def tracks_compare(self):
        os.system('cls')
        print('Проверка отсутствующих треков на сервере\n')

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

        spt = SpotifyTracks.SpTracks(spl)
        spt.start()
        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        comp = TracksComparator.Comparator(set(), spotify_tracks, tracks_info)

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
