import SettingsStorage
import os
import SpotifyTracks
import LocalTracks
import win32com.client
import time
import TracksComparator
import SpLogin
import Utils


class TracksSyncing:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._spotify_login = SpLogin.SpLogin()

    def tracks_syncing(self):
        os.system('cls')
        print('Синхронизация треков с аккаунтом\n')

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
                            print('Синхронизация отменена')
                            time.sleep(1)

                            return
                    case 'n':
                        print('Синхронизация отменена')
                        time.sleep(1)
                        return
                    case _:
                        print('Ошибка ввода')

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

        spt = SpotifyTracks.SpTracks(spl)
        try:
            spt.start()
        except SpotifyTracks.TracksGetError:
            print('Ошибка при получении треков из spotify')
            time.sleep(1)
            return

        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)

        if self._settings.get_setting('auto_comp') == 'True':
            server_missing_tracks = comp.get_server_missing_tracks()

            if len(server_missing_tracks) == 0:
                print('\nТреки на сервере синхронизированы\n')
            else:
                print('\nСписок отсутствующих треков на сервере:\n')
                for i, track in enumerate(server_missing_tracks):
                    print(f'{i + 1}) {track}')
                print()

                print('[1] - Продолжить синхронизацию треков\n'
                      '[2] - Добавить треки в серверный игнор лист\n\n'
                      '[b] - Назад')

                while True:
                    match input('> '):
                        case '1':
                            break

                        case '2':
                            name = input('Введи название трека\n> ')

                            try:
                                self._settings.add_track_to_server_ignore(name)
                                print(f'Трек "{name}" добавлен в игнор лист')

                            except SettingsStorage.AlreadyExistsError:
                                print(f'Трек "{name}" уже добавлен в игнор лист')

                        case 'b':
                            print('Синхронизация прекращена')
                            time.sleep(1)
                            return

                        case _:
                            print('Ошибка ввода')

        local_missing_tracks = comp.get_local_missing_tracks()

        print()
        if len(local_missing_tracks) == 0:
            print('Локальные треки синхронизированы')
            time.sleep(1)
            return

        print('Список отсутствующих локальных треков:\n')
        for i, track in enumerate(local_missing_tracks):
            print(f'{i + 1}) {track}')

        print('\n[1] - Скачать отсутствующие треки\n'
              '[2] - Добавить треки в локальный игнор лист (новые треки будут сразу проигнорированы при загрузке)\n\n'
              '[b] - Назад')

        new_tracks = False
        while True:
            match input('> '):
                case '1':
                    break

                case '2':
                    name = input('Введи название трека\n> ')

                    try:
                        self._settings.add_track_to_local_ignore(name)
                        print(f'Трек "{name}" добавлен в игнор лист')
                        new_tracks = True

                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек "{name}" уже добавлен в игнор лист')

                case 'b':
                    print('Загрузка отменена')
                    time.sleep(1)
                    return
                case _:

                    print('Ошибка ввода')

        if new_tracks:
            spt.refresh_track_list()

            comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)
            local_missing_tracks = comp.get_local_missing_tracks()

        Utils.start_playlist_download([(track, self._settings.get_setting('path_for_sync'), local_missing_tracks[track]) for track in local_missing_tracks])
