__all__ = [
    'Ui'
]

import MainPage
import Update
import argparse
import customtkinter as ctk
from PIL import ImageTk, Image
import time
from Ui import Utils


class Ui(ctk.CTk):
    def __init__(self):
        super().__init__()

        self._window_width = 600
        self._window_height = 400

        self.minsize(self._window_width, self._window_height)
        self.title('Spotify downloader')
        self.geometry(self._pos_for_window())
        self.iconbitmap(Utils.resource_path('icon.ico'))
        self.resizable(False, False)

        self._create_splash_screen()

        self._main_page = MainPage.MainPage()
        self._update = Update.Update(self, self._update_callback)

        parser = argparse.ArgumentParser()
        parser.add_argument('-U', type=str, help='Path to previous executable file')
        self._args = parser.parse_args()

    def _update_callback(self, need_exit):
        if need_exit:
            self.quit()
        else:
            self._update.destroy()

        self.resizable(True, True)

    def _pos_for_window(self):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()

        x = (ws // 2) - (self._window_width // 2)
        y = (hs // 2) - (self._window_height // 2)

        return '%dx%d+%d+%d' % (self._window_width, self._window_height, x, y)

    def _create_splash_screen(self):
        self.wm_attributes('-topmost', True)
        self.overrideredirect(True)

        logo_width = 200
        logo_height = 200

        self._default_bg_color = self['bg']
        self.config(bg='')

        self.wm_attributes('-transparentcolor', '#FFFFFE')
        self._logo = ctk.CTkCanvas(self, width=logo_width, height=logo_height, highlightthickness=0, bg='#FFFFFE')

        logo = Image.open(Utils.resource_path('icon.ico')).resize((logo_width, logo_height))
        self._logo_image = ImageTk.PhotoImage(logo)
        self._logo.create_image(0, 0, anchor=ctk.NW, image=self._logo_image)

        self._logo.pack(anchor=ctk.CENTER, expand=True)

    def _delete_splash_screen(self):
        while not self.winfo_ismapped():
            time.sleep(0.2)

        start_time = time.time()

        need_update = self._update.update_check()

        if (time_left := time.time() - start_time) < 1.5:
            time.sleep((1500 - int(time_left * 1000)) / 1000)

        self._logo.destroy()
        self.config(bg=self._default_bg_color)
        self.overrideredirect(False)
        self.wm_attributes('-topmost', False)

        if need_update:
            self._update.pack(fill='both', expand=True, anchor='c')
        else:
            self.resizable(True, True)

    def _install_update(self):
        while not self.winfo_ismapped():
            time.sleep(0.2)

        self._logo.destroy()
        self.config(bg=self._default_bg_color)
        self.overrideredirect(False)
        self.wm_attributes('-topmost', False)

        self._update.pack(fill='both', expand=True, anchor='c')
        self._update.install(self._args.U)

        self.quit()

    def start(self):
        if self._args.U is not None:
            self.after(1500, self._install_update)
            self.mainloop()

            return

        # self._main_page.main_page()

        self.after(200, self._delete_splash_screen)
        self.mainloop()
