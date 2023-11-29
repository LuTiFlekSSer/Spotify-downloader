__all__ = [
    'Ui'
]

import MainPage
import Update
import argparse
import customtkinter as ctk
from PIL import ImageTk, Image
import time


class Ui(ctk.CTk):
    def __init__(self):
        super().__init__()

        self._window_width = 640
        self._window_height = 480

        self.minsize(self._window_width, self._window_height)
        self.title('Spotify downloader')
        self.geometry(self._pos_for_window())
        self.iconbitmap('icon.ico')

        self._main_page = MainPage.MainPage()
        self._update = Update.Update()

        parser = argparse.ArgumentParser()
        parser.add_argument('-U', type=str, help='Path to previous executable file')
        self._args = parser.parse_args()

    def _pos_for_window(self):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()

        x = (ws // 2) - (self._window_width // 2)
        y = (hs // 2) - (self._window_height // 2)

        return '%dx%d+%d+%d' % (self._window_width, self._window_height, x, y)

    def _create_splash_screen(self):
        self.overrideredirect(True)
        logo_width = 200
        logo_height = 200

        self._default_bg_color = self['bg']
        self.config(bg='')

        self.wm_attributes('-transparentcolor', '#FFFFFE')
        self._logo = ctk.CTkCanvas(self, width=logo_width, height=logo_height, highlightthickness=0, bg='#FFFFFE')

        logo = Image.open('icon.ico').resize((logo_width, logo_height))
        self._logo_image = ImageTk.PhotoImage(logo)

        self._logo.create_image(0, 0, anchor=ctk.NW, image=self._logo_image)

        self._logo.pack(anchor=ctk.CENTER, expand=True)

    def _delete_splash_screen(self):
        while not self.winfo_ismapped():
            time.sleep(0.2)

        start_time = time.time()

        if self._update.start():  # todo сначала просто чекнуть, есть ли обнова
            return

        if (time_left := time.time() - start_time) < 1.5:
            time.sleep((1500 - int(time_left * 1000)) / 1000)

        self._logo.destroy()
        self.config(bg=self._default_bg_color)
        self.overrideredirect(False)

    def start(self):
        if self._args.U is not None:
            self._update.install(self._args.U)
            return

        # self._main_page.main_page()

        self.after(0, self._create_splash_screen)
        self.after(200, self._delete_splash_screen)
        self.mainloop()
