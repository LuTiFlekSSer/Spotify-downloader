import SettingsStorage
import os
import SpotifyTracks
import LocalTracks
import time
import TracksComparator
import SpLogin
import Utils
import customtkinter as ctk
from PIL import Image
import Locales


class TracksSyncing(ctk.CTkFrame):
    def __init__(self, master, callback):
        super().__init__(master)

        self._settings = SettingsStorage.Settings()
        self._locales = Locales.Locales()
        self._callback = callback

        self._title_frame = ctk.CTkFrame(self)

        self._sync_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/back.png')), size=(20, 20))
        self._back_button = ctk.CTkButton(
            self._title_frame,
            image=self._sync_image,
            command=lambda: callback(self),
            text='',
            width=20,
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
        )

        self._sync_title = ctk.CTkLabel(
            self._title_frame,
            text=self._locales.get_string('sync_title'),
            font=('Arial', 23, 'bold')
        )

        self._sync_frame = ctk.CTkFrame(self)
        self._spotify_login = SpLogin.SpLogin(self._sync_frame, self._login_close_callback)

        self._sync_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self._sync_frame.grid_rowconfigure((0, 1, 2), weight=1)

        self._title_frame.grid_columnconfigure(0, weight=1)
        self._title_frame.grid_rowconfigure(0, weight=1)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._sync_title.grid(row=0, column=0, sticky='ns')
        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._title_frame.grid(row=0, column=0, padx=5, pady=5, sticky='new', ipady=4)
        self._sync_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

    def _login_close_callback(self):
        self._spotify_login.grid_forget()

        self._start_sync()

    def initialize(self):
        self._spotify_login.grid_forget()

        if (res := self._spotify_login.spotify_login()) is None:
            self._spotify_login.grid(row=1, column=1, sticky='nsew')

        elif not res:
            self._callback(self)

        else:
            self._start_sync()

    def _start_sync(self):
        pass

    def tracks_syncing(self):
        def print_menu():
            os.system('cls')
            print(Utils.cyan('Синхронизация треков с аккаунтом\n'))

        print_menu()

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            if not Utils.set_sync_path(print_menu):
                return

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        spl = self._spotify_login.spotify_login()

        if spl is None:
            return

        print_menu()

        spt = SpotifyTracks.SpTracks(spl)
        try:
            spt.start()
        except SpotifyTracks.TracksGetError:
            print(Utils.red('\nОшибка при получении треков из spotify'))
            time.sleep(1)
            return

        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

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
                            self._settings.save()

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
                        self._settings.save()

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
                                      [(track, self._settings.get_setting('path_for_sync'), local_missing_tracks[track]) for track in local_missing_tracks],
                                      True)
