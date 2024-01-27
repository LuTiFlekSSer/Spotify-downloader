import CTkTable
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
from CTkMessagebox import CTkMessagebox
import threading
import pyperclip


class TracksSyncing(ctk.CTkFrame):
    def __init__(self, master, exit_callback, busy_callback):
        super().__init__(master)

        self._settings = SettingsStorage.Settings()
        self._locales = Locales.Locales()
        self._exit_callback = exit_callback
        self._busy_callback = busy_callback

        self._title_frame = ctk.CTkFrame(self)

        self._sync_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/back.png')), size=(20, 20))
        self._back_button = ctk.CTkButton(
            self._title_frame,
            image=self._sync_image,
            command=lambda: exit_callback(self),
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
        self._spotify_login = SpLogin.SpLogin(self._sync_frame, self.initialize)

        self._table_frame = ctk.CTkScrollableFrame(
            self._sync_frame,
            fg_color=self._title_frame.cget('fg_color')
        )

        self._table = CTkTable.CTkTable(
            self._table_frame,
            width=10,
            wraplength=250,
            command=lambda x: pyperclip.copy(x['value']),
            values=[['№', self._locales.get_string('title'), self._locales.get_string('status')]]
        )

        self._input_frame = ctk.CTkFrame(
            self._sync_frame,
            fg_color=self._title_frame.cget('fg_color')
        )

        self._get_tracks_frame = ctk.CTkFrame(
            self._input_frame,
            fg_color=self._input_frame.cget('fg_color')
        )

        self._next_button = ctk.CTkButton(
            self._input_frame,
            text=self._locales.get_string('next'),
            command=self._start_sync
        )

        self._progress_bar = ctk.CTkProgressBar(self._get_tracks_frame)

        self._current_step_title = ctk.CTkLabel(
            self._get_tracks_frame,
            font=('Arial', 17, 'bold')
        )

        self._missing_tracks_frame = ctk.CTkFrame(
            self._input_frame,
            fg_color=self._input_frame.cget('fg_color')
        )

        self._missing_tracks_title = ctk.CTkTextbox(
            self._missing_tracks_frame,
            font=('Arial', 17, 'bold'),
            wrap='word',
            height=51,
            activate_scrollbars=False,
            padx=0,
            pady=0,
            fg_color=self._input_frame.cget('fg_color')
        )
        self._missing_tracks_title.configure(state='disabled')

        self._missing_tracks_description = ctk.CTkTextbox(
            self._missing_tracks_frame,
            wrap='word',
            height=75,
            activate_scrollbars=False,
            padx=0,
            pady=0,
            fg_color=self._input_frame.cget('fg_color')
        )
        self._missing_tracks_description.configure(state='disabled')

        self._input_ignore_list = ctk.CTkEntry(self._missing_tracks_frame)

        self._add_ignore_tracks_button = ctk.CTkButton(
            self._missing_tracks_frame,
            text=self._locales.get_string('add')
        )

        self._sync_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self._sync_frame.grid_rowconfigure((0, 1, 2), weight=1)

        self._title_frame.grid_columnconfigure(0, weight=1)
        self._title_frame.grid_rowconfigure(0, weight=1)

        self._table_frame.grid_columnconfigure(0, weight=1)
        self._table_frame.grid_rowconfigure(0, weight=1)

        self._input_frame.grid_rowconfigure((0, 1, 2), weight=1)
        self._input_frame.grid_columnconfigure(0, weight=1)

        self._get_tracks_frame.rowconfigure((0, 1), weight=1)
        self._get_tracks_frame.columnconfigure(0, weight=1)

        self._missing_tracks_frame.columnconfigure(0, weight=1)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._sync_title.grid(row=0, column=0, sticky='ns')
        self._title_frame.grid(row=0, column=0, padx=5, pady=5, sticky='new', ipady=4)
        self._sync_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self._table.grid(row=0, column=0, sticky='nsew')
        self._get_tracks_frame.grid(row=1, column=0, sticky='we')
        self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
        self._current_step_title.grid(row=0, column=0, padx=5, pady=5)
        self._missing_tracks_title.grid(row=0, column=0, pady=5, sticky='we')
        self._missing_tracks_description.grid(row=1, column=0, pady=5, sticky='we')

    def initialize(self):
        self._sync_frame.configure(fg_color=self._title_frame.cget('fg_color'))
        self._table_frame.grid_forget()
        self._input_frame.grid_forget()

        self._spotify_login.grid_forget()

        if (res := self._spotify_login.spotify_login()) is None:
            self._spotify_login.grid(row=1, column=1, sticky='nsew')

        elif not res:
            self._exit_callback(self)

        else:
            self._progress_bar.set(0)
            self._current_step_title.configure(text=self._locales.get_string('getting_tracks_from_disk'))
            self._back_button.grid(row=0, column=0, sticky='w', padx=2)
            self._next_button.grid_forget()
            self._missing_tracks_frame.grid_forget()
            self._input_ignore_list.grid_forget()
            self._add_ignore_tracks_button.grid_forget()
            self._update_table([])
            self._input_ignore_list.delete(0, 'end')

            self._table_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0), columnspan=2, rowspan=3)
            self._input_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5), rowspan=3)

            self._get_tracks_frame.grid(row=1, column=0)
            self._sync_frame.configure(fg_color=self.cget('fg_color'))

            self._start_sync()

    def _start_sync(self):
        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            result = CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('path_error'),
                icon='cancel',
                option_1=self._locales.get_string('yes'),
                option_2=self._locales.get_string('no'),
                topmost=False
            ).get()

            if result == self._locales.get_string('yes'):

                if not Utils.set_sync_path(self._locales.get_string('choose_folder')):
                    self._exit_callback(self)
                    return
            else:
                self._exit_callback(self)
                return

        progress_value = 0
        self._local_tracks = None

        def _get_local_tracks():
            nonlocal progress_value

            lct = LocalTracks.LcTracks()

            for i, total in lct.get_tracks_from_folder():
                progress_value = Utils.map_value(i, total)

            self._local_tracks = lct.get_local_tracks()

        self._back_button.grid_forget()
        self._busy_callback(True)

        local_tracks_thread = threading.Thread(target=_get_local_tracks)
        local_tracks_thread.start()

        while local_tracks_thread.is_alive():
            time.sleep(0.01)

            self._progress_bar.set(progress_value)
            self.update()

        self._progress_bar.set(0)
        self._current_step_title.configure(text=self._locales.get_string('getting_tracks_from_spotify'))

        spl = self._spotify_login.spotify_login()
        if spl is None:
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('authorization_error'),
                icon='cancel',
                topmost=False
            ).get()

            self._exit_callback(self)
            return

        self._spotify_tracks = None
        self._tracks_info = None
        self._spt = None
        progress_value = 0

        def _get_spotify_tracks():
            nonlocal progress_value

            self._spt = SpotifyTracks.SpTracks(spl)
            try:
                for i, total in self._spt.start():
                    progress_value = Utils.map_value(i, total)

            except SpotifyTracks.TracksGetError:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('get_spotify_tracks_error'),
                    icon='cancel',
                    topmost=False
                ).get()

                self._exit_callback(self)
                return

            self._spotify_tracks = self._spt.get_spotify_tracks()
            self._tracks_info = self._spt.get_tracks_info()

        spotify_tracks_thread = threading.Thread(target=_get_spotify_tracks)
        spotify_tracks_thread.start()

        while spotify_tracks_thread.is_alive():
            time.sleep(0.01)

            self._progress_bar.set(progress_value)
            self.update()

        self._comp = TracksComparator.Comparator(self._local_tracks, self._spotify_tracks, self._tracks_info)

        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._next_button.grid(row=2, column=0, sticky='se', pady=5, padx=5)
        self._missing_tracks_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)

        if self._settings.get_setting('auto_comp') == 'True':
            self._server_missing_tracks = self._comp.get_server_missing_tracks()

            self._set_missing_title(self._locales.get_string('missing_spotify_tracks'))

            if len(self._server_missing_tracks) == 0:
                self._set_missing_description(self._locales.get_string('no_missing_tracks'))
            else:
                self._set_missing_description(self._locales.get_string('find_missing_tracks'))

                def _add_server_ignore():
                    track_name = self._input_ignore_list.get().strip()

                    try:
                        Utils.add_tracks_to_ignore(self._server_missing_tracks, self._settings.add_track_to_server_ignore, track_name)
                        self._settings.save()
                        self._server_missing_tracks = self._comp.get_server_missing_tracks(refresh=True)

                        self._input_ignore_list.delete(0, 'end')

                        self._update_table(self._server_missing_tracks)
                    except ValueError:
                        CTkMessagebox(
                            title=self._locales.get_string('error'),
                            message=self._locales.get_string('input_error'),
                            icon='cancel',
                            topmost=False
                        ).get()

                    except IndexError:
                        CTkMessagebox(
                            title=self._locales.get_string('error'),
                            message=self._locales.get_string('index_error'),
                            icon='cancel',
                            topmost=False
                        ).get()

                self._add_ignore_tracks_button.configure(command=_add_server_ignore)

                self._input_ignore_list.grid(row=2, column=0, pady=5, sticky='we')
                self._add_ignore_tracks_button.grid(row=3, column=0, pady=5, sticky='e')

                self._update_table(self._server_missing_tracks)

            self._next_button.configure(command=self._sync_local)
        else:
            self._sync_local()

    def _sync_local(self):
        self._set_missing_title(self._locales.get_string('missing_local_tracks'))

        self._local_missing_tracks = self._comp.get_local_missing_tracks()

        if len(self._local_missing_tracks) == 0:
            self._set_missing_description(self._locales.get_string('no_missing_tracks'))

            self._next_button.grid_forget()
            self._update_table([])
            self._input_ignore_list.grid_forget()
            self._add_ignore_tracks_button.grid_forget()
        else:
            self._set_missing_description(self._locales.get_string('find_missing_tracks'))

            def _add_local_ignore():
                track_name = self._input_ignore_list.get().strip()

                try:
                    Utils.add_tracks_to_ignore(sorted(self._local_missing_tracks), self._settings.add_track_to_local_ignore, track_name)
                    self._settings.save()

                    self._spt.refresh_track_list()
                    self._local_missing_tracks = self._comp.get_local_missing_tracks(refresh=True)

                    self._input_ignore_list.delete(0, 'end')

                    self._update_table(sorted(self._local_missing_tracks))
                except ValueError:
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('input_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

                except IndexError:
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('index_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

            self._add_ignore_tracks_button.configure(command=_add_local_ignore)

            self._input_ignore_list.grid(row=2, column=0, pady=5, sticky='we')
            self._add_ignore_tracks_button.grid(row=3, column=0, pady=5, sticky='e')

            self._update_table(sorted(self._local_missing_tracks))

            self._next_button.configure(command=self._start_download)

    def _start_download(self):
        pass

    def _create_values_for_table(self, values):
        return ([['№', self._locales.get_string('title'), self._locales.get_string('status')]] +
                [[i + 1, track, self._locales.get_string('state_missing')] for i, track in enumerate(values)])

    def _update_table(self, values):
        self._table.delete_rows(range(len(self._table.get())))

        for value in self._create_values_for_table(values):
            self._table.add_row(value, width=10)

    def _set_missing_title(self, text):
        self._missing_tracks_title.configure(state='normal')

        self._missing_tracks_title.bind('<MouseWheel>', lambda event: 'break')

        self._missing_tracks_title.delete('0.0', 'end')
        self._missing_tracks_title.insert('end', text)

        self._missing_tracks_title.tag_config('text', justify='center')
        self._missing_tracks_title.tag_add('text', '0.0', 'end')

        self._missing_tracks_title.configure(state='disabled')

    def _set_missing_description(self, text):
        self._missing_tracks_description.configure(state='normal')

        self._missing_tracks_description.bind('<MouseWheel>', lambda event: 'break')

        self._missing_tracks_description.delete('0.0', 'end')
        self._missing_tracks_description.insert('end', text)

        self._missing_tracks_description.configure(state='disabled')

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
