import CTkTable

import DownloaderPool
import SettingsStorage
import os
import SpotifyTracks
import LocalTracks
import time

import TrackDownloader
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
        self._completed_tracks = {}
        self._downloading = False

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
            values=self._create_values_for_table([])
        )
        self._page = 0
        self._table_limit = 30

        self._next_table_page_button = ctk.CTkButton(
            self._table_frame,
            text=self._locales.get_string('forward'),
            command=self._next_page
        )
        self._back_table_page_button = ctk.CTkButton(
            self._table_frame,
            text=self._locales.get_string('back'),
            command=self._previous_page,
            state='disabled'
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

        self._table_frame.grid_columnconfigure((0, 1), weight=1)
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
        self._table.grid(row=0, column=0, sticky='nsew', columnspan=2)
        self._get_tracks_frame.grid(row=1, column=0, sticky='we', padx=5, pady=5)
        self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
        self._current_step_title.grid(row=0, column=0, padx=5, pady=5)
        self._missing_tracks_title.grid(row=0, column=0, pady=5, sticky='we')
        self._missing_tracks_description.grid(row=1, column=0, pady=5, sticky='we')

    def _next_page(self):
        self._table_frame._parent_canvas.yview_moveto(0)
        self._page += 1

        self._table.update_values(
            self._create_values_for_table(
                self._table_data[self._table_limit * self._page:self._table_limit * (self._page + 1)],
                self._table_limit * self._page
            )
        )

        self._back_table_page_button.configure(state='normal')
        if self._table_limit * (self._page + 1) >= len(self._table_data):
            self._next_table_page_button.configure(state='disabled')

    def _previous_page(self):
        self._table_frame._parent_canvas.yview_moveto(0)
        self._page -= 1

        self._table.update_values(
            self._create_values_for_table(
                self._table_data[self._table_limit * self._page:self._table_limit * (self._page + 1)],
                self._table_limit * self._page
            )
        )

        self._next_table_page_button.configure(state='normal')
        if self._page == 0:
            self._back_table_page_button.configure(state='disabled')

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
            self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
            self._current_step_title.configure(text=self._locales.get_string('getting_tracks_from_disk'))
            self._back_button.grid(row=0, column=0, sticky='w', padx=2)
            self._next_button.grid_forget()
            self._next_button.configure(text=self._locales.get_string('next'))
            self._missing_tracks_frame.grid_forget()
            self._input_ignore_list.grid_forget()
            self._add_ignore_tracks_button.grid_forget()
            self._update_table([])
            self._input_ignore_list.delete(0, 'end')
            self._next_table_page_button.grid_forget()
            self._back_table_page_button.grid_forget()
            self._completed_tracks = {}
            self._table_frame._parent_canvas.yview_moveto(0)
            self._downloading = False

            self._table_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0), columnspan=2, rowspan=3)
            self._input_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5), rowspan=3)

            self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')
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
        exit_flag = False

        def _get_spotify_tracks():
            nonlocal progress_value, exit_flag

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

                exit_flag = True

            self._spotify_tracks = self._spt.get_spotify_tracks()
            self._tracks_info = self._spt.get_tracks_info()

        spotify_tracks_thread = threading.Thread(target=_get_spotify_tracks)
        spotify_tracks_thread.start()

        while spotify_tracks_thread.is_alive():
            time.sleep(0.01)

            self._progress_bar.set(progress_value)
            self.update()

        if exit_flag:
            return self._exit_callback(self)

        self._comp = TracksComparator.Comparator(self._local_tracks, self._spotify_tracks, self._tracks_info)

        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._next_button.grid(row=2, column=0, sticky='s', pady=5, padx=5)
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

                        if len(self._server_missing_tracks) == 0:
                            self._set_missing_description(self._locales.get_string('no_missing_tracks'))
                            self._input_ignore_list.grid_forget()
                            self._add_ignore_tracks_button.grid_forget()

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

                self.update()

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

                    if len(self._local_missing_tracks) == 0:
                        self._set_missing_description(self._locales.get_string('no_missing_tracks'))
                        self._input_ignore_list.grid_forget()
                        self._add_ignore_tracks_button.grid_forget()
                        self._next_button.grid_forget()

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

            self.update()

            self._update_table(sorted(self._local_missing_tracks))

            self._next_button.configure(command=self._start_download)

    def _start_download(self):
        self._downloading = True
        self._back_button.grid_forget()
        self._missing_tracks_frame.grid_forget()
        self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')

        for cell_index in range(self._table_limit * self._page, self._table_limit * (self._page + 1)):
            try:
                self._table.insert(cell_index % self._table_limit + 1, 2, self._locales.get_string('downloading'))
            except KeyError:
                pass
        self.update()

        self._tracks_for_downloading = [(track, self._settings.get_setting('path_for_sync'), self._local_missing_tracks[track]) for track in sorted(self._local_missing_tracks)]

        self._pp = DownloaderPool.PlaylistPool(True)
        self._completed_count = 0
        self._completed_tracks = {}

        def _download():
            for track, track_status in self._pp.start(self._tracks_for_downloading):
                self._completed_count += 1
                self._completed_tracks[track] = track_status

        def _start():
            self._progress_bar.set(0)
            self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
            self._current_step_title.configure(text=self._locales.get_string('tracks_downloading'))
            self._back_button.grid_forget()
            self._next_button.configure(command=self._pp.stop, text=self._locales.get_string('stop'))

            download_thread = threading.Thread(target=_download)
            download_thread.start()

            last_iter = False
            while download_thread.is_alive() or last_iter:
                time.sleep(0.01)

                for track_index in range(self._table_limit * self._page, self._table_limit * (self._page + 1)):
                    if track_index in self._completed_tracks:
                        status = self._get_status_str(self._completed_tracks[track_index])

                        index_on_page = track_index % self._table_limit
                        self._table.insert(index_on_page + 1, 2, status)

                self._progress_bar.set(Utils.map_value(self._completed_count, len(self._tracks_for_downloading)))
                self.update()

                if last_iter:
                    break

                if not download_thread.is_alive():
                    last_iter = True

            self._back_button.grid(row=0, column=0, sticky='w', padx=2)
            self._next_button.configure(text=self._locales.get_string('retry'), command=_retry)
            self._progress_bar.grid_forget()
            self._current_step_title.configure(text=self._locales.get_string('completed'))

        def _retry():
            pp_status = self._pp.pool_status()
            self._tracks_for_downloading = [track for track in self._tracks_for_downloading if track[0] not in pp_status['ok']['list']]

            if len(self._tracks_for_downloading) == 0:
                CTkMessagebox(
                    title=self._locales.get_string('retry_title'),
                    message=self._locales.get_string('retry_description'),
                    icon='info',
                    topmost=False
                ).get()

                return

            self._pp.clear_tracks_with_error()

            self._completed_count = 0
            self._completed_tracks = {}

            self._update_table([track for track, _, _ in self._tracks_for_downloading])
            _start()

        _start()

    def _create_values_for_table(self, values, offset=0):
        table_values = [['№', self._locales.get_string('title'), self._locales.get_string('status')]]

        for i, track in enumerate(values):
            if self._downloading:
                status = self._locales.get_string('downloading')
            else:
                status = self._locales.get_string('state_missing')

            if offset + i in self._completed_tracks:
                status = self._get_status_str(self._completed_tracks[offset + i])

            table_values.append([offset + i + 1, track, status])

        return table_values

    def _get_status_str(self, status):
        match status:
            case TrackDownloader.Status.OK:
                return self._locales.get_string('downloaded')
            case TrackDownloader.Status.GET_ERR | TrackDownloader.Status.API_ERR:
                return self._locales.get_string('download_error')
            case TrackDownloader.Status.JPG_ERR:
                return self._locales.get_string('jpg_error')
            case TrackDownloader.Status.NF_ERR:
                return self._locales.get_string('nf_error')
            case TrackDownloader.Status.TAG_ERR:
                return self._locales.get_string('tag_error')
            case TrackDownloader.Status.CANCELLED:
                return self._locales.get_string('cancelled')

    def _update_table(self, values):
        self._table_data = values
        rows_count = len(self._table.get())

        was_updated = False
        tmp_values = []

        for i, value in enumerate(self._create_values_for_table(self._table_data[:self._table_limit])):
            if i < rows_count:
                tmp_values.append(value)
            else:
                if not was_updated:
                    was_updated = True
                    self._table.update_values(tmp_values)

                self._table.add_row(value, width=10)

        if not was_updated:
            self._table.update_values(tmp_values)

        if len(self._table_data) > self._table_limit:
            self._next_table_page_button.grid(row=1, column=1, sticky='e', padx=5, pady=5)
            self._back_table_page_button.grid(row=1, column=0, sticky='w', padx=5, pady=5)

            self._next_table_page_button.configure(state='normal')
            self._back_table_page_button.configure(state='disabled')

            self._page = 0
        else:
            self._next_table_page_button.grid_forget()
            self._back_table_page_button.grid_forget()

            self._table.delete_rows([i for i in range(len(values) + 1, len(self._table.get()))])

    def _set_missing_title(self, text):
        self._missing_tracks_title.configure(state='normal')

        self._missing_tracks_title.bind('<MouseWheel>', lambda event: 'break')

        self._missing_tracks_title.delete('0.0', 'end')
        self._missing_tracks_title.insert('end', text)

        self._missing_tracks_title.tag_config('text', justify='center')
        self._missing_tracks_title.tag_add('text', '0.0', 'end')

        self._missing_tracks_title.configure(state='disabled')
        self.update()

    def _set_missing_description(self, text):
        self._missing_tracks_description.configure(state='normal')

        self._missing_tracks_description.bind('<MouseWheel>', lambda event: 'break')

        self._missing_tracks_description.delete('0.0', 'end')
        self._missing_tracks_description.insert('end', text)

        self._missing_tracks_description.configure(state='disabled')
