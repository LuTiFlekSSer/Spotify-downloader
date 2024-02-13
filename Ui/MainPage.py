import TracksProcessing
import Utils
import customtkinter as ctk
import Locales
from PIL import Image


class MainPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self._locales = Locales.Locales()
        self._busy_flag = False

        self._tracks_syncing = TracksProcessing.TracksProcessing(self, self._exit_callback, self._busy_callback, Utils.DownloadMode.SYNC)
        self._tracks_compare = TracksProcessing.TracksProcessing(self, self._exit_callback, self._busy_callback, Utils.DownloadMode.COMP)
        self._playlist_download = TracksProcessing.TracksProcessing(self, self._exit_callback, self._busy_callback, Utils.DownloadMode.PLAYLIST)
        # self._multiple_tracks_download = MultipleTracksDownload.MultipleTracksDownload()

        self._sync_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/sync.png')), size=(30, 30))
        self._check_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/check.png')), size=(30, 30))
        self._playlist_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/playlist.png')), size=(30, 30))
        self._multiple_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/track.png')), size=(30, 30))

        self._menu_frame = ctk.CTkFrame(self)
        self._sync_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('sync_tracks'),
            image=self._sync_image,
            compound='top',
            command=self._open_tracks_syncing,

        )
        self._tracks_check_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('check_tracks'),
            image=self._check_image,
            compound='top',
            command=self._open_tracks_compare,

        )
        self._playlist_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('download_playlist'),
            image=self._playlist_image,
            compound='top',
            command=self._open_playlist_download,

        )
        self._multiple_tracks_button = ctk.CTkButton(
            self._menu_frame,
            text=self._locales.get_string('download_tracks'),
            image=self._multiple_image,
            compound='top',
            command=...,

        )

        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self._menu_frame.grid(row=1, column=1)
        self._sync_button.grid(row=0, column=0, padx=10, pady=10)
        self._tracks_check_button.grid(row=0, column=1, padx=10, pady=10)
        self._playlist_button.grid(row=1, column=0, padx=10, pady=10)
        self._multiple_tracks_button.grid(row=1, column=1, padx=10, pady=10)

    def _open_tracks_syncing(self):
        self._menu_frame.grid_forget()

        self._tracks_syncing.grid(row=0, column=0, sticky='nsew', rowspan=3, columnspan=3)
        self._tracks_syncing.initialize()

    def _open_tracks_compare(self):
        self._menu_frame.grid_forget()

        self._tracks_compare.grid(row=0, column=0, sticky='nsew', rowspan=3, columnspan=3)
        self._tracks_compare.initialize()

    def _open_playlist_download(self):
        self._menu_frame.grid_forget()

        self._playlist_download.grid(row=0, column=0, sticky='nsew', rowspan=3, columnspan=3)
        self._playlist_download.initialize()

    def get_busy_state(self):
        return self._busy_flag

    def _busy_callback(self, value):
        self._busy_flag = value

    def _exit_callback(self, current_frame):
        current_frame.grid_forget()
        self._busy_flag = False

        self._menu_frame.grid(row=1, column=1)
