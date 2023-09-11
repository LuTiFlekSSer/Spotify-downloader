import os
import SpotifyTracks
import TracksComparator
import SettingsStorage
import time
import SpLogin
import win32com.client
import LocalTracks
import Utils


class TracksCompare:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._spotify_login = SpLogin.SpLogin()

    def tracks_compare(self):
        os.system('cls')
        print(Utils.cyan('Проверка отсутствующих треков на сервере\n'))

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            print(Utils.red(f'{Utils.Colors.BLINK}Не задан путь к папке для синхронизации, задать сейчас?') + Utils.yellow(' (y - да, n - нет)'))

            while True:
                match input('> '):
                    case 'y':

                        try:
                            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                            self._settings.change_setting('path_for_sync', directory)

                            print(f'{Utils.green("Путь изменен на:")} {directory}\n')

                            break
                        except Exception:
                            print(Utils.red('Проверка отменена'))
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
        spt.start()
        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)

        server_missing_tracks = comp.get_server_missing_tracks()

        if len(server_missing_tracks) == 0:
            print(Utils.green('\nТреки на сервере синхронизированы\n'))
        else:
            print(Utils.yellow('\nСписок отсутствующих треков на сервере:\n'))
            for i, track in enumerate(server_missing_tracks):
                print(f'{i + 1}) {track}')
        print()
        print(f'{Utils.blue("[1]")} - Добавить треки в серверный игнор лист\n\n'
              f'{Utils.purple("[b]")} - назад')

        while True:
            match Utils.g_input('> '):
                case '1':
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
                    break
                case _:
                    print(Utils.red('Ошибка ввода'))
