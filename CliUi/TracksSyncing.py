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
        print(Utils.cyan('Синхронизация треков с аккаунтом\n'))

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            print(Utils.red(f'{Utils.Colors.BLINK}Не задан путь к папке для синхронизации, задать сейчас?') + Utils.yellow(' (y - да, n - нет)'))

            while True:
                match Utils.g_input('> '):
                    case 'y':

                        try:
                            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                            self._settings.change_setting('path_for_sync', directory)

                            print(f'{Utils.green("Путь изменен на:")} {directory}\n')

                            break
                        except Exception:
                            print(Utils.red('Синхронизация отменена'))
                            time.sleep(1)

                            return
                    case 'n':
                        print(Utils.green('Возврат в меню'))
                        time.sleep(1)

                        return
                    case _:
                        print(Utils.red('Ошибка ввода'))

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

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

        if self._settings.get_setting('auto_comp') == 'True':
            server_missing_tracks = comp.get_server_missing_tracks()

            if len(server_missing_tracks) == 0:
                print(Utils.green('\nТреки на сервере синхронизированы\n'))
                time.sleep(1)
            else:
                print(Utils.yellow('\nСписок отсутствующих треков на сервере:\n'))
                for i, track in enumerate(server_missing_tracks):
                    print(f'{i + 1}) {track}')
                print()

                print(f'{Utils.blue("[1]")} - Продолжить синхронизацию треков\n'
                      f'{Utils.blue("[2]")} - Добавить треки в серверный игнор лист\n\n'
                      f'{Utils.purple("[b]")} - Назад')

                while True:
                    match Utils.g_input('> '):
                        case '1':
                            break

                        case '2':
                            print('Введи название трека')
                            name = Utils.g_input('> ')

                            try:
                                self._settings.add_track_to_server_ignore(name)
                                print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} добавлен в игнор лист{Utils.Colors.END}')

                            except SettingsStorage.AlreadyExistsError:
                                print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} уже был добавлен игнор лист{Utils.Colors.END}')

                        case 'b':
                            print(Utils.green('Возврат в меню'))
                            time.sleep(1)
                            return

                        case _:
                            print(Utils.red('Ошибка ввода'))

        local_missing_tracks = comp.get_local_missing_tracks()

        print()
        if len(local_missing_tracks) == 0:
            print(Utils.green('Локальные треки синхронизированы'))
            time.sleep(1)
            return

        print(Utils.yellow('Список отсутствующих локальных треков:\n'))
        for i, track in enumerate(local_missing_tracks):
            print(f'{i + 1}) {track}')

        print(f'\n{Utils.blue("[1]")} - Скачать отсутствующие треки\n'
              f'{Utils.blue("[2]")} - Добавить треки в локальный игнор лист (новые треки будут сразу проигнорированы при загрузке)\n\n'
              f'{Utils.purple("[b]")} - Назад')

        new_tracks = False
        while True:
            match Utils.g_input('> '):
                case '1':
                    break

                case '2':
                    print('Введи название трека')
                    name = Utils.g_input('> ')

                    try:
                        self._settings.add_track_to_local_ignore(name)
                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} добавлен в игнор лист{Utils.Colors.END}')
                        new_tracks = True

                    except SettingsStorage.AlreadyExistsError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} уже был добавлен игнор лист{Utils.Colors.END}')

                case 'b':
                    print(Utils.green('Возврат в меню'))
                    time.sleep(1)
                    return
                case _:
                    print(Utils.red('Ошибка ввода'))

        if new_tracks:
            spt.refresh_track_list()

            comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)
            local_missing_tracks = comp.get_local_missing_tracks()

        Utils.start_playlist_download([(track, self._settings.get_setting('path_for_sync'), local_missing_tracks[track]) for track in local_missing_tracks])
