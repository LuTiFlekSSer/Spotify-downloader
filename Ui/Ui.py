__all__ = [
    'Ui'
]

import os
import MainPage
import Update
import argparse
import customtkinter as ctk
from PIL import ImageTk, Image
import time
from Ui import Utils
import CTkMenuBar
import Locales
import subprocess
import SettingsStorage
from CTkMessagebox import CTkMessagebox
from Ui import SetSettings


class Ui(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode('Dark')

        self._settings = SettingsStorage.Settings()

        try:
            window_size = self._settings.get_setting('window_size')
            self._window_width, self._window_height = map(int, window_size.split('*'))
        except SettingsStorage.NotFoundError:
            self._window_width = 640
            self._window_height = 400

        self.minsize(640, 400)
        self.title('Spotify downloader')
        self.geometry(self._pos_for_window())
        self.iconbitmap(Utils.resource_path('icons/icon.ico'))
        self.resizable(False, False)

        self._create_splash_screen()

        parser = argparse.ArgumentParser()
        parser.add_argument('-U', type=str, help='Path to previous executable file')
        parser.add_argument('-F', help='Force update app')
        self._args = parser.parse_args()

        self._update = Update.Update(self, self._update_callback)
        self._locales = Locales.Locales()

    def _update_callback(self, need_exit):
        if need_exit:
            self.quit()
        else:
            self._update.destroy()
            self._create_menu_bar()

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

        logo = Image.open(Utils.resource_path('icons/icon.ico')).resize((logo_width, logo_height))
        self._logo_image = ImageTk.PhotoImage(logo)
        self._logo.create_image(0, 0, anchor=ctk.NW, image=self._logo_image)

        self._logo.pack(anchor=ctk.CENTER, expand=True)

    def _delete_splash_screen(self):
        while not self.winfo_ismapped():
            time.sleep(0.2)

        start_time = time.time()

        if self._args.F is not None:
            force = True
        else:
            force = False

        need_update = self._update.update_check(force)

        if (time_left := time.time() - start_time) < 1.5:
            time.sleep((1500 - int(time_left * 1000)) / 1000)

        self._logo.destroy()
        self.config(bg=self._default_bg_color)
        self.overrideredirect(False)
        self.wm_attributes('-topmost', False)

        if need_update:
            self._update.pack(fill='both', expand=True, anchor='c')

            if force:
                self._update.download()
        else:
            self._create_menu_bar()

        self.protocol("WM_DELETE_WINDOW", self._close_callback)

    def _create_menu_bar(self):
        self.resizable(True, True)

        self._menu_bar = CTkMenuBar.CTkMenuBar(self, bg_color=self.cget('bg'))
        self._file_button = self._menu_bar.add_cascade(self._locales.get_string('menu_file'))

        self._file_dropdown = CTkMenuBar.CustomDropdownMenu(widget=self._file_button)
        self._file_dropdown.add_option(option=self._locales.get_string('open_sync_dir'), command=self._open_sync_folder)
        self._file_dropdown.add_separator()
        self._file_dropdown.add_option(option=self._locales.get_string('open_settings'), command=self._open_settings)  # todo чекать, не запущен ли режим в mainpage
        self._file_dropdown.add_option(option=self._locales.get_string('check_for_updates'), command=self._check_for_updates)  # todo чекать, не запущен ли режим в mainpage
        self._file_dropdown.add_separator()
        self._file_dropdown.add_option(option=self._locales.get_string('exit'), command=self._close_callback)

        self._main_page = MainPage.MainPage(self)
        self._main_page.pack(fill='both', expand=True)

    def _open_settings(self):
        if not hasattr(self, '_set_settings'):
            self._set_settings = SetSettings.SetSettings(self, self._close_settings)

        if self._set_settings.winfo_ismapped():
            return

        self._main_page.pack_forget()
        self._set_settings.pack(fill='both', expand=True)

    def _close_settings(self):
        self._set_settings.pack_forget()
        self._main_page.pack(fill='both', expand=True)

    def _check_for_updates(self):
        result = self._update.update_check()

        if result:
            result = CTkMessagebox(
                title=self._locales.get_string('update?'),
                message=self._locales.get_string('update_title'),
                icon='question',
                option_1=self._locales.get_string('yes'),
                option_2=self._locales.get_string('no'),
                topmost=False
            ).get()

            if result == self._locales.get_string('yes'):
                path = Utils.get_executable_path()

                if path.endswith('.py'):
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('run_as_script_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

                    return

                subprocess.Popen(
                    f'{path} -F 1',
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                self._close_callback()
        else:
            CTkMessagebox(
                title=self._locales.get_string('check'),
                message=self._locales.get_string('last_update_installed'),
                icon='check',
                topmost=False
            ).get()

    def _open_sync_folder(self):
        path = self._settings.get_setting('path_for_sync')

        if path == '' or not os.path.exists(path):
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('sync_dir_error'),
                icon='cancel',
                topmost=False
            ).get()
        else:
            subprocess.Popen(f'explorer "{path}"')

    def _install_update(self):
        while not self.winfo_ismapped():
            time.sleep(0.2)

        self._logo.destroy()
        self.config(bg=self._default_bg_color)
        self.overrideredirect(False)
        self.wm_attributes('-topmost', False)

        self._update.pack(fill='both', expand=True, anchor='c')
        self._update.install(self._args.U)

        self._close_callback()

    def _close_callback(self):
        width, height = self.winfo_width(), self.winfo_height()

        self._settings.change_setting('window_size', f'{width}*{height}')

        self.destroy()

    def start(self):
        if self._args.U is not None:
            self.after(1500, self._install_update)
            self.mainloop()

            return

        self.after(200, self._delete_splash_screen)
        self.mainloop()
