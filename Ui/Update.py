__all__ = [
    'Update'
]

import Updater
import CompatibilityChecker
import time
import Utils
import SettingsStorage
import subprocess
import threading
import customtkinter as ctk
import Locales
from CTkMessagebox import CTkMessagebox
from PIL import ImageTk, Image
import ctypes
import locale


class Update(ctk.CTkFrame):
    def __init__(self, master, callback):
        super().__init__(master, fg_color=master.cget('fg_color'))
        self._locales = Locales.Locales()

        self._callback = callback

        self._cc = CompatibilityChecker.CompatibilityChecker()
        self._updater = Updater.Updater()

        self._ss = SettingsStorage.Settings()
        self._db_check()

        self._progress_bar = ctk.CTkProgressBar(self, determinate_speed=0.1)
        self._progress_bar.set(0)
        self._update_title = ctk.CTkLabel(self, text=self._locales.get_string('update_title'), font=('Arial', 20, 'bold'))
        self._button_frame = ctk.CTkFrame(self, fg_color=ctk.CTkFrame(self)['bg'])
        self._button_yes = ctk.CTkButton(
            self._button_frame,
            text=self._locales.get_string('yes'),
            command=self.download,
            fg_color='green',
            hover_color='dark green'
        )
        self._button_no = ctk.CTkButton(
            self._button_frame,
            text=self._locales.get_string('no'),
            fg_color='red',
            command=lambda: self._callback(False),
            hover_color='dark red'
        )
        self._logo = ctk.CTkCanvas(self, width=100, height=100, highlightthickness=0, bg=self._button_frame['bg'])

        logo = Image.open(Utils.resource_path('icons/icon.ico')).resize((100, 100))
        self._logo_image = ImageTk.PhotoImage(logo)
        self._logo.create_image(0, 0, anchor=ctk.NW, image=self._logo_image)

        self._logo.pack(anchor='center', pady=(70, 10))
        self._update_title.pack(anchor='center', pady=10)
        self._button_frame.pack(anchor='center', pady=20)
        self._button_no.pack(side='left', padx=10)
        self._button_yes.pack(side='right', padx=10)

    def _db_check(self):
        if self._cc.need_db_update():
            self._cc.update_db()

        language = self._ss.get_setting('language')

        if language == 'None':
            windll = ctypes.windll.kernel32
            system_language = locale.windows_locale[windll.GetUserDefaultUILanguage()]

            if system_language == 'ru_RU':
                self._ss.change_setting('language', 'ru')
                language = 'ru'
            else:
                self._ss.change_setting('language', 'en')
                language = 'en'

        Locales.Locales.set_language(language)

    def update_check(self, force=False):
        if self._ss.get_setting('auto_update') == 'False' and force is False:
            return False

        try:
            result = False

            def _check():
                nonlocal result

                try:
                    result = self._updater.need_app_update()
                except Updater.UpdateCheckError:
                    result = False

            check_thread = threading.Thread(target=_check)
            check_thread.start()

            while check_thread.is_alive():
                self.update()
                time.sleep(0.01)

            return result

        except Exception:
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('update_check_error'),
                icon='cancel',
                topmost=False
            ).get()

            return False

    def download(self):
        self._button_frame.destroy()
        self._progress_bar.pack(anchor='center', pady=10)
        self._update_title.configure(text=self._locales.get_string('downloading_update'))

        progress_value = 0

        exit_flag = False

        def _start_download():
            nonlocal progress_value, exit_flag

            try:
                self._updater.start_download()

                total_size = self._updater.get_total_size()
                for i in self._updater.download_update():
                    progress_value = Utils.map_value(i, total_size)

            except Exception:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('update_download_error'),
                    icon='cancel',
                    topmost=False
                ).get()
                exit_flag = True

        download_thread = threading.Thread(target=_start_download)
        download_thread.start()

        while download_thread.is_alive():
            time.sleep(0.01)

            self._progress_bar.set(progress_value)

            self.update()

        if exit_flag:
            return self._callback(False)

        try:
            self._updater.start_update()
        except Exception:
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('update_install_error'),
                icon='cancel',
                topmost=False
            ).get()

            return self._callback(False)

        return self._callback(True)

    def install(self, path_to_exe=None):
        self._button_frame.destroy()
        self._update_title.configure(text=self._locales.get_string('installing_update'))

        if path_to_exe is None:
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('update_install_error'),
                icon='cancel',
                topmost=False
            ).get()

            return

        self._progress_bar.configure(mode='indeterminate')
        self._progress_bar.pack(anchor='center', pady=10)
        self._progress_bar.start()

        result = False

        def _install():
            nonlocal result

            try:
                time.sleep(2)

                self._updater.install_update(path_to_exe)
                result = True

            except Exception:
                CTkMessagebox(
                    title=self._locales.get_string('error'),
                    message=self._locales.get_string('update_install_error'),
                    icon='cancel',
                    topmost=False
                ).get()

        install_thread = threading.Thread(target=_install)
        install_thread.start()

        while install_thread.is_alive():
            if result:
                self._update_title.configure(text=self._locales.get_string('update_installed'))

                self._progress_bar.stop()
                self._progress_bar.destroy()

                break

            self.update()
            time.sleep(0.01)

        if result:
            subprocess.Popen(path_to_exe, creationflags=subprocess.CREATE_NEW_CONSOLE)
