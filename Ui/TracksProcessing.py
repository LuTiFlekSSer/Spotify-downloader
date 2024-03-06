import win32com.client
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
from PIL import Image, ImageTk
import Locales
from CTkMessagebox import CTkMessagebox
import threading
import pyperclip
import CustomTable
from urllib.parse import urlparse
import requests


class TracksProcessing(ctk.CTkFrame):
    def __init__(self, master, exit_callback, busy_callback, mode):
        super().__init__(master)

        self._settings = SettingsStorage.Settings()
        self._locales = Locales.Locales()
        self._exit_callback = exit_callback
        self._busy_callback = busy_callback
        self._completed_tracks = {}
        self._downloading = False
        self._mode = mode
        self._playlist_error = True
        self._playlist = []
        self._path = ''

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

        title_text = ''

        match self._mode:
            case Utils.DownloadMode.COMP:
                title_text = self._locales.get_string('compare_title')
            case Utils.DownloadMode.SYNC:
                title_text = self._locales.get_string('sync_title')
            case Utils.DownloadMode.PLAYLIST:
                title_text = self._locales.get_string('playlist_title')
            case Utils.DownloadMode.MULTIPLE:
                title_text = self._locales.get_string('multiple_title')

        self._sync_title = ctk.CTkLabel(
            self._title_frame,
            text=title_text,
            font=('Arial', 23, 'bold')
        )

        self._sync_frame = ctk.CTkFrame(self)
        self._spotify_login = SpLogin.SpLogin(self._sync_frame, self.initialize)

        self._table_frame = ctk.CTkScrollableFrame(
            self._sync_frame,
            fg_color=self._title_frame.cget('fg_color')
        )

        self._table = CustomTable.CustomTable(
            self._table_frame,
            width=10,
            wraplength=250,
            command=lambda x: pyperclip.copy(x['value']),
            values=self._create_values_for_table([]),
            max_rows=31,
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

        self._tracks_frame = ctk.CTkFrame(
            self._input_frame,
            fg_color=self._input_frame.cget('fg_color')
        )

        self._tracks_title = ctk.CTkTextbox(
            self._tracks_frame,
            font=('Arial', 17, 'bold'),
            wrap='word',
            height=51,
            activate_scrollbars=False,
            padx=0,
            pady=0,
            fg_color=self._input_frame.cget('fg_color')
        )
        self._tracks_title.configure(state='disabled')

        self._tracks_description = ctk.CTkTextbox(
            self._tracks_frame,
            wrap='word',
            height=75,
            activate_scrollbars=False,
            padx=0,
            pady=0,
            fg_color=self._input_frame.cget('fg_color'),
            state='disabled'
        )
        self._path_textbox = ctk.CTkTextbox(
            self._tracks_frame,
            wrap='none',
            height=25,
            padx=0,
            pady=0,
            fg_color=self._input_frame.cget('fg_color'),
            state='disabled'
        )

        self._no_missing_canvas = ctk.CTkCanvas(
            self._tracks_frame,
            width=150,
            height=150,
            highlightthickness=0,
            bg=self._tracks_frame.cget('bg_color')[1],
        )

        image = Image.open(Utils.resource_path('icons/galochka.png')).resize((150, 150))
        self._no_missing_image = ImageTk.PhotoImage(image)
        self._no_missing_canvas.create_image(0, 0, anchor=ctk.NW, image=self._no_missing_image)

        self._input_entry = ctk.CTkEntry(self._tracks_frame)

        self._input_button = ctk.CTkButton(
            self._tracks_frame,
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

        self._tracks_frame.columnconfigure(0, weight=1)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._sync_title.grid(row=0, column=0, sticky='ns')
        self._title_frame.grid(row=0, column=0, padx=5, pady=5, sticky='new', ipady=4)
        self._sync_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self._table.grid(row=0, column=0, sticky='nsew', columnspan=2)
        self._get_tracks_frame.grid(row=1, column=0, sticky='we', padx=5, pady=5)
        self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
        self._current_step_title.grid(row=0, column=0, padx=5, pady=5)
        self._tracks_title.grid(row=0, column=0, pady=5, sticky='we')
        self._tracks_description.grid(row=1, column=0, pady=5, sticky='we')

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

    def _set_page(self, page):
        self._page = page

        self._table.update_values(
            self._create_values_for_table(
                self._table_data[self._table_limit * self._page:self._table_limit * (self._page + 1)],
                self._table_limit * self._page
            )
        )

        if self._table_limit * (self._page + 1) < len(self._table_data):
            self._next_table_page_button.configure(state='normal')

        if self._page != 0:
            self._back_table_page_button.configure(state='normal')

    def initialize(self):
        self._sync_frame.configure(fg_color=self._title_frame.cget('fg_color'))
        self._table_frame.grid_forget()
        self._input_frame.grid_forget()
        self._spotify_login.grid_forget()

        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        if not (self._mode == Utils.DownloadMode.MULTIPLE or self._mode == Utils.DownloadMode.PLAYLIST):
            if (res := self._spotify_login.spotify_login()) is None and (self._mode == Utils.DownloadMode.COMP or self._mode == Utils.DownloadMode.SYNC):
                return self._spotify_login.grid(row=1, column=1, sticky='nsew')

            elif not res:
                return self._exit_callback(self)

        self._progress_bar.set(0)
        self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
        self._progress_bar.configure(mode='determinate')
        self._next_button.grid_forget()
        self._next_button.configure(text=self._locales.get_string('next'))
        self._tracks_frame.grid_forget()
        self._input_entry.grid_forget()
        self._input_button.grid_forget()
        self._update_table([])
        self._input_entry.delete(0, 'end')
        self._next_table_page_button.grid_forget()
        self._back_table_page_button.grid_forget()
        self._completed_tracks = {}
        self._table_frame._parent_canvas.yview_moveto(0)
        self._downloading = False
        self._no_missing_canvas.grid_forget()
        self._input_button.configure(text=self._locales.get_string('add'))
        self._playlist = []
        self._path_textbox.grid_forget()
        self._page = 0
        self._next_button.configure(state='normal')
        self._back_button.configure(state='normal')
        self._back_button.configure(command=lambda: self._exit_callback(self))

        if (path := self._settings.get_setting('path_for_sync')) != '' or not os.path.exists(path):
            self._set_path(f"{self._locales.get_string('current_path')} {path}")
            self._path = path
        else:
            self._set_path(f"{self._locales.get_string('current_path')} {self._locales.get_string('not_specified')}")
            self._path = ''

        self._table_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0), columnspan=2, rowspan=3)
        self._input_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5), rowspan=3)

        self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')
        self._sync_frame.configure(fg_color=self.cget('fg_color'))

        match self._mode:
            case Utils.DownloadMode.SYNC | Utils.DownloadMode.COMP:
                self._current_step_title.configure(text=self._locales.get_string('getting_tracks_from_disk'))

                self._start_sync()

            case Utils.DownloadMode.PLAYLIST:
                self._start_playlist_download()

            case Utils.DownloadMode.MULTIPLE:
                self._start_multiple_download()

    def _start_multiple_download(self):
        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._next_button.grid(row=2, column=0, sticky='s', pady=5, padx=5)
        self._get_tracks_frame.grid_forget()
        self._tracks_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)
        self._input_entry.grid(row=2, column=0, pady=5, sticky='we')
        self._input_button.grid(row=3, column=0, pady=5, sticky='e')
        self._update_table([])
        self._input_button.configure(text=self._locales.get_string('confirm'))
        self._tracks_description.configure(height=25)

        self._path_input()

    def _initialize_multiple_pool(self):
        self._busy_callback(True)
        self._path_textbox.grid_forget()
        self._input_entry.grid(row=2, column=0, pady=5, sticky='we')
        self._tracks_description.grid(row=1, column=0, pady=5, sticky='we')

        self._set_title(self._locales.get_string('links_input'))
        self._set_description(self._locales.get_string('input_link'))

        self._mtp = DownloaderPool.MultipleTracksPool(self._path)
        self._downloading = True

        def _add_track():
            link = self._input_entry.get().strip()
            if urlparse(link).scheme:
                self._input_button.configure(state='disabled')
                self._next_button.configure(state='disabled')
                self._back_button.configure(state='disabled')
                self._input_entry.configure(state='disabled')
                self.update()
                track_name = ''

                def _add_to_mtp():
                    nonlocal track_name
                    track_name = self._mtp.add(link)

                add_thread = threading.Thread(target=_add_to_mtp)
                add_thread.start()

                while add_thread.is_alive():
                    self.update()
                    time.sleep(0.01)

                self._input_button.configure(state='normal')
                self._next_button.configure(state='normal')
                self._back_button.configure(state='normal')
                self._input_entry.configure(state='normal')
                self.update()

                self._playlist.append(track_name)

                tmp_page = self._page
                self._update_table(self._playlist)
                self._set_page(tmp_page)

            else:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('link_error'),
                    icon='cancel',
                    topmost=False
                ).get()

            self._input_entry.delete(0, 'end')

        self._input_button.configure(command=_add_track, text=self._locales.get_string('add'))
        self._next_button.configure(command=self._stop_multiple, text=self._locales.get_string('finish_download'))
        self._back_button.configure(command=lambda: self._stop_multiple(True))

        while self._downloading:
            self.update()
            time.sleep(0.01)

            self._update_table_for_multiple()

        self._update_table_for_multiple()

    def _update_table_for_multiple(self):
        for row, track in enumerate(self._table_data[self._table_limit * self._page:self._table_limit * (self._page + 1)]):
            try:
                status = self._get_status_str(self._mtp.pool_status()['all_tracks'][track])
                self._table.insert(row + 1, 2, status)
            except KeyError:
                pass

    def _stop_multiple(self, back_clicked=False):
        self._downloading = False

        self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
        self._progress_bar.configure(mode='indeterminate')
        self._next_button.grid_forget()
        self._back_button.grid_forget()
        self._progress_bar.start()
        self._current_step_title.configure(text=self._locales.get_string('multiple_completion'))
        self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')
        self._tracks_frame.grid_forget()

        while self._mtp.launched() != 0:
            self.update()
            time.sleep(0.01)

        self._progress_bar.stop()
        self._progress_bar.configure(mode='determinate')
        self._progress_bar.grid_forget()
        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._back_button.configure(command=lambda: self._exit_callback(self))
        self._current_step_title.configure(text=self._locales.get_string('completed'))
        self._next_button.grid(row=2, column=0, sticky='s', pady=5, padx=5)
        self.update()

        if back_clicked:
            return self._exit_callback(self)

        def _retry_multiple():
            self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
            self._progress_bar.configure(mode='indeterminate')
            self._current_step_title.configure(text=self._locales.get_string('retry_title'))
            self._next_button.grid_forget()
            self._progress_bar.start()
            self._downloading = True

            mtp_status = self._mtp.pool_status()
            links = []
            track_names = []

            for error_type in ['jpg_err', 'tag_err', 'get_err', 'nf_err']:
                if mtp_status[error_type]['quantity'] == 0:
                    continue

                track_buffer = mtp_status[error_type]['list'].copy()

                mtp_status[error_type]['list'].clear()
                mtp_status[error_type]['quantity'] -= len(track_buffer)

                for track in track_buffer:
                    links.append(track['link'])
                    track_names.append(track['name'])

            if mtp_status['link_err']['quantity'] != 0:
                track_buffer = mtp_status['link_err']['list'].copy()

                mtp_status['link_err']['list'].clear()
                mtp_status['link_err']['quantity'] -= len(track_buffer)

                for track in track_buffer:
                    links.append(track)
                    track_names.append(track)

            self._mtp.pool_status()['all_tracks'].clear()
            self._update_table(track_names)
            track_names.clear()

            def _retry_thread():
                for link in links:
                    track_names.append(self._mtp.add(link))

            retry_thread = threading.Thread(target=_retry_thread)
            retry_thread.start()

            flag = False

            while retry_thread.is_alive() or self._mtp.launched() != 0:
                time.sleep(0.01)
                self.update()

                if not retry_thread.is_alive() and not flag:
                    flag = True
                    self._update_table(track_names)

                self._update_table_for_multiple()

            self._update_table_for_multiple()

            self._progress_bar.grid_forget()
            self._progress_bar.configure(mode='determinate')
            self._current_step_title.configure(text=self._locales.get_string('completed'))
            self._progress_bar.stop()
            self._next_button.grid(row=2, column=0, sticky='s', pady=5, padx=5)
            self._stop_multiple()

        for error_type in ['jpg_err', 'tag_err', 'get_err', 'nf_err', 'link_err']:
            if self._mtp.pool_status()[error_type]['quantity'] != 0:
                self._next_button.configure(text=self._locales.get_string('retry'), command=_retry_multiple)
                return

        self._next_button.configure(text=self._locales.get_string('go_to_menu'), command=lambda: self._exit_callback(self))

    def _start_playlist_download(self):
        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._next_button.grid(row=2, column=0, sticky='s', pady=5, padx=5)
        self._get_tracks_frame.grid_forget()
        self._tracks_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)
        self._input_entry.grid(row=2, column=0, pady=5, sticky='we')
        self._input_button.grid(row=3, column=0, pady=5, sticky='e')
        self._update_table([])
        self._input_button.configure(text=self._locales.get_string('confirm'))
        self._tracks_description.configure(height=25)

        def _parse_link():
            link = self._input_entry.get().strip()
            self._update_table([])

            playlist_id = urlparse(link).path

            if '/' not in playlist_id:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('link_error'),
                    icon='cancel',
                    topmost=False
                ).get()

                self._playlist_error = True

                return

            playlist_id = playlist_id[playlist_id.rfind('/') + 1:]

            self._playlist = []
            error = False

            def _get_tracks():
                nonlocal error

                offset = 0
                try:
                    while True:
                        playlist_info = requests.get(
                            f'https://api.spotifydown.com/trackList/playlist/{playlist_id}?offset={offset}',
                            headers=TrackDownloader.Downloader.headers
                        ).json()

                        if not playlist_info['success']:
                            error = True

                            return

                        self._playlist += playlist_info['trackList']

                        if playlist_info['nextOffset'] is None:
                            break

                        offset = playlist_info['nextOffset']

                except Exception:
                    error = True

                    return

            get_tracks_thread = threading.Thread(target=_get_tracks)
            get_tracks_thread.start()

            self._progress_bar.configure(mode='indeterminate')
            self._progress_bar.start()
            self._current_step_title.configure(text=self._locales.get_string('getting_playlist_info'))
            self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')
            self._tracks_frame.grid_forget()

            while get_tracks_thread.is_alive():
                time.sleep(0.01)

                self.update()

            self._progress_bar.stop()
            self._progress_bar.configure(mode='determinate')
            self._get_tracks_frame.grid_forget()
            self._tracks_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)

            if error:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('link_work_error'),
                    icon='cancel',
                    topmost=False
                ).get()

                self._playlist_error = True

                return

            separator = '\u29f8'
            self._update_table([f"{track['title']} - {separator.join([aut.strip() for aut in track['artists'].split(',')])}" for track in self._playlist])

            self._input_entry.delete(0, 'end')
            self._playlist_error = False

        self._input_button.configure(command=_parse_link)
        self._next_button.configure(command=self._path_input)
        self._set_title(self._locales.get_string('playlist_link_input'))
        self._set_description(self._locales.get_string('playlist_link_description'))

    def _path_input(self):
        if self._mode == Utils.DownloadMode.PLAYLIST:
            if len(self._playlist) == 0:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('playlist_len_error'),
                    icon='cancel',
                    topmost=False
                ).get()

                return
            elif self._playlist_error:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('playlist_error'),
                    icon='cancel',
                    topmost=False
                ).get()

                return

            self._next_button.configure(command=self._download_playlist)

        elif self._mode == Utils.DownloadMode.MULTIPLE:
            self._next_button.configure(command=self._initialize_multiple_pool)

        self._set_title(self._locales.get_string('path_input'))
        self._tracks_description.grid_forget()
        self._path_textbox.grid(row=1, column=0, pady=5, sticky='we')
        self._input_entry.grid_forget()

        def _change_path():
            try:
                self._path = (win32com.client.Dispatch('Shell.Application').
                              BrowseForFolder(0, self._locales.get_string('choose_folder'), 16, "").Self.path)

                self._set_path(f"{self._locales.get_string('current_path')} {self._path}")
            except Exception:
                pass

        self._input_button.configure(text=self._locales.get_string('change'), command=_change_path)

    def _download_playlist(self):
        self._busy_callback(True)

        if self._path == '':
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('path_not_specified'),
                icon='cancel',
                topmost=False
            ).get()

            return

        self._downloading = True
        self._back_button.grid_forget()
        self._tracks_frame.grid_forget()
        self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')

        self._tracks_for_downloading = [TrackDownloader.create_download_query(track, self._path) for track in self._playlist]

        self._pp = DownloaderPool.PlaylistPool(False)
        self._completed_count = 0
        self._completed_tracks = {}

        self._start()

    def _set_path(self, text):
        self._path_textbox.configure(state='normal')
        self._path_textbox.delete('0.0', 'end')
        self._path_textbox.insert('end', text)
        self._path_textbox.configure(state='disabled')

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
        self._get_tracks_frame.grid_forget()
        self._tracks_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)

        if self._settings.get_setting('auto_comp') == 'True' or self._mode == Utils.DownloadMode.COMP:
            self._server_missing_tracks = self._comp.get_server_missing_tracks()

            self._set_title(self._locales.get_string('missing_spotify_tracks'))

            if len(self._server_missing_tracks) == 0:
                self._set_description(self._locales.get_string('no_missing_tracks'))
                self._no_missing_canvas.grid(row=2, column=0)
            else:
                self._set_description(self._locales.get_string('find_missing_tracks'))

                def _add_server_ignore():
                    track_name = self._input_entry.get().strip()

                    try:
                        Utils.add_tracks_to_ignore(self._server_missing_tracks, self._settings.add_track_to_server_ignore, track_name)
                        self._settings.save()
                        self._server_missing_tracks = self._comp.get_server_missing_tracks(refresh=True)

                        self._input_entry.delete(0, 'end')

                        self._update_table(self._server_missing_tracks)

                        if len(self._server_missing_tracks) == 0:
                            self._set_description(self._locales.get_string('no_missing_tracks'))
                            self._input_entry.grid_forget()
                            self._input_button.grid_forget()
                            self._no_missing_canvas.grid(row=2, column=0)

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

                self._input_button.configure(command=_add_server_ignore)

                self._input_entry.grid(row=2, column=0, pady=5, sticky='we')
                self._input_button.grid(row=3, column=0, pady=5, sticky='e')

                self.update()

                self._update_table(self._server_missing_tracks)

            if self._mode == Utils.DownloadMode.COMP:
                self._next_button.configure(text=self._locales.get_string('go_to_menu'), command=lambda: self._exit_callback(self))
            else:
                self._next_button.configure(command=self._sync_local)
        else:
            self._sync_local()

    def _sync_local(self):
        self._no_missing_canvas.grid_forget()
        self._set_title(self._locales.get_string('missing_local_tracks'))

        self._local_missing_tracks = self._comp.get_local_missing_tracks()

        if len(self._local_missing_tracks) == 0:
            self._set_description(self._locales.get_string('no_missing_tracks'))

            self._next_button.configure(text=self._locales.get_string('go_to_menu'), command=lambda: self._exit_callback(self))
            self._update_table([])
            self._input_entry.grid_forget()
            self._input_button.grid_forget()
            self._no_missing_canvas.grid(row=2, column=0)
        else:
            self._set_description(self._locales.get_string('find_missing_tracks'))

            def _add_local_ignore():
                track_name = self._input_entry.get().strip()

                try:
                    Utils.add_tracks_to_ignore(sorted(self._local_missing_tracks), self._settings.add_track_to_local_ignore, track_name)
                    self._settings.save()

                    self._spt.refresh_track_list()
                    self._local_missing_tracks = self._comp.get_local_missing_tracks(refresh=True)

                    self._input_entry.delete(0, 'end')

                    self._update_table(sorted(self._local_missing_tracks))

                    if len(self._local_missing_tracks) == 0:
                        self._set_description(self._locales.get_string('no_missing_tracks'))
                        self._input_entry.grid_forget()
                        self._input_button.grid_forget()
                        self._next_button.configure(text=self._locales.get_string('go_to_menu'), command=lambda: self._exit_callback(self))
                        self._no_missing_canvas.grid(row=2, column=0)

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

            self._input_button.configure(command=_add_local_ignore)

            self._input_entry.grid(row=2, column=0, pady=5, sticky='we')
            self._input_button.grid(row=3, column=0, pady=5, sticky='e')

            self.update()

            self._update_table(sorted(self._local_missing_tracks))

            self._next_button.configure(command=self._start_download)

    def _start_download(self):
        self._tracks_for_downloading = [(track, self._settings.get_setting('path_for_sync'), self._local_missing_tracks[track]) for track in sorted(self._local_missing_tracks)]

        self._pp = DownloaderPool.PlaylistPool(True)
        self._completed_count = 0
        self._completed_tracks = {}

        self._start()

    def _download(self):
        for track, track_status in self._pp.start(self._tracks_for_downloading):
            self._completed_count += 1
            self._completed_tracks[track] = track_status

    def _stop_download(self):
        result = CTkMessagebox(
            title=self._locales.get_string('stop_download_title'),
            message=self._locales.get_string('stop_download_description'),
            icon='question',
            option_1=self._locales.get_string('yes'),
            option_2=self._locales.get_string('no'),
            topmost=False
        ).get()

        if result == self._locales.get_string('yes'):
            self._pp.stop()
            self._next_button.configure(state='disabled')

    def _start(self):
        self._downloading = True
        self._back_button.grid_forget()
        self._tracks_frame.grid_forget()
        self._get_tracks_frame.grid(row=1, column=0, padx=5, pady=5, sticky='we')

        for cell_index in range(self._table_limit * self._page, self._table_limit * (self._page + 1)):
            try:
                if self._table.get(cell_index % self._table_limit + 1, 0) == ' ':
                    continue

                self._table.insert(cell_index % self._table_limit + 1, 2, self._locales.get_string('downloading'))
            except KeyError:
                pass
        self.update()

        self._progress_bar.set(0)
        self._progress_bar.grid(row=1, column=0, padx=5, pady=5)
        self._current_step_title.configure(text=self._locales.get_string('tracks_downloading'))
        self._back_button.grid_forget()
        self._next_button.configure(command=self._stop_download, text=self._locales.get_string('stop'))

        download_thread = threading.Thread(target=self._download)
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
        self._next_button.configure(state='normal')

        pp_status = self._pp.pool_status()
        self._tracks_for_downloading = [track for track in self._tracks_for_downloading if track[0] not in pp_status['ok']['list']]

        if len(self._tracks_for_downloading) == 0:
            self._next_button.configure(text=self._locales.get_string('go_to_menu'), command=lambda: self._exit_callback(self))
        else:
            self._next_button.configure(text=self._locales.get_string('retry'), command=self._retry)

        self._progress_bar.grid_forget()
        self._current_step_title.configure(text=self._locales.get_string('completed'))

    def _retry(self):
        self._pp.clear_tracks_with_error()

        self._completed_count = 0
        self._completed_tracks = {}

        self._update_table([track for track, _, _ in self._tracks_for_downloading])

        self._table_frame._parent_canvas.yview_moveto(0)

        self._start()

    def _create_values_for_table(self, values, offset=0):
        table_values = [['№', self._locales.get_string('title'), self._locales.get_string('status')]]

        for i, track in enumerate(values):
            if self._downloading:
                if self._mode == Utils.DownloadMode.MULTIPLE and track in self._mtp.pool_status()['all_tracks']:
                    status = self._get_status_str(self._mtp.pool_status()['all_tracks'][track])
                else:
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
            case TrackDownloader.Status.LINK_ERR:
                return self._locales.get_string('multiple_link_error')

    def _update_table(self, values):
        self._table_data = values.copy()
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

    def _set_title(self, text):
        self._tracks_title.configure(state='normal')

        self._tracks_title.bind('<MouseWheel>', lambda event: 'break')

        self._tracks_title.delete('0.0', 'end')
        self._tracks_title.insert('end', text)

        self._tracks_title.tag_config('text', justify='center')
        self._tracks_title.tag_add('text', '0.0', 'end')

        self._tracks_title.configure(state='disabled')
        self.update()

    def _set_description(self, text):
        self._tracks_description.configure(state='normal')

        self._tracks_description.bind('<MouseWheel>', lambda event: 'break')

        self._tracks_description.delete('0.0', 'end')
        self._tracks_description.insert('end', text)

        self._tracks_description.tag_config('text', justify='center')
        self._tracks_description.tag_add('text', '0.0', 'end')

        self._tracks_description.configure(state='disabled')
