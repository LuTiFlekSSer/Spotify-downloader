import SettingsStorage
import os
import time
import win32com.client
import Utils
import customtkinter as ctk
import Locales
from PIL import Image
from CTkMessagebox import CTkMessagebox


def _print_settings():
    os.system('cls')
    print(f'{Utils.cyan("Настройки")}\n\n'
          f'{Utils.blue("[1]")} - Поменять кол-во потоков для загрузки треков\n'
          f'{Utils.blue("[2]")} - Поменять путь для синхронизации треков\n'
          f'{Utils.blue("[3]")} - Автоматически проверять отсутствующие треки на сервере при синхронизации\n'
          f'{Utils.blue("[4]")} - Очистить данные для входа в аккаунт\n'
          f'{Utils.blue("[5]")} - Управление локальным игнор листом\n'
          f'{Utils.blue("[6]")} - Управление серверным игнор листом\n'
          f'{Utils.blue("[7]")} - Автоматическая проверка обновлений\n'
          f'{Utils.blue("[8]")} - Перезапись существующих треков при загрузке\n\n'
          f'{Utils.purple("[c]")} - Очистка ввода\n'
          f'{Utils.purple("[b]")} - Назад\n', end='')


class SetSettings(ctk.CTkFrame):
    def __init__(self, master, callback):
        super().__init__(master)

        self._locales = Locales.Locales()
        self._settings = SettingsStorage.Settings()

        self._buttons_container = ctk.CTkScrollableFrame(self, width=220)
        self._title_frame = ctk.CTkFrame(self)

        self._sync_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/back.png')), size=(20, 20))
        self._back_button = ctk.CTkButton(
            self._title_frame,
            image=self._sync_image,
            command=callback,
            text='',
            width=20,
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
        )
        self._settings_title = ctk.CTkLabel(self._title_frame, text=self._locales.get_string('settings'), font=('Arial', 25, 'bold'))

        self._set_threads_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('set_threads'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._set_sync_dir_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('set_sync_dir'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._set_auto_compare_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('set_auto_tracks_compare'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._clear_data_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('clear_data'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._local_ignore_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('local_ignore'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._server_ignore_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('server_ignore'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._update_check_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('auto_check_update'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._rewrite_tracks_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('rewrite_tracks'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )
        self._set_language_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('language'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w'
        )

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._title_frame.grid_columnconfigure(0, weight=1)
        self._title_frame.grid_rowconfigure(0, weight=1)
        self._buttons_container.grid_columnconfigure(0, weight=1)

        self._settings_title.grid(row=0, column=0, sticky='ns')
        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._title_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe', columnspan=2, ipady=1)

        self._set_threads_button.grid(row=0, column=0, sticky='ew')
        self._set_sync_dir_button.grid(row=1, column=0, sticky='ew')
        self._set_auto_compare_button.grid(row=2, column=0, sticky='ew')
        self._clear_data_button.grid(row=3, column=0, sticky='ew')
        self._local_ignore_button.grid(row=4, column=0, sticky='ew')
        self._server_ignore_button.grid(row=5, column=0, sticky='ew')
        self._update_check_button.grid(row=6, column=0, sticky='ew')
        self._rewrite_tracks_button.grid(row=7, column=0, sticky='ew')
        self._set_language_button.grid(row=8, column=0, sticky='ew')
        self._buttons_container.grid(row=1, column=0, sticky='nsw', pady=5, padx=5)

        self._current_frame = None
        self._settings_set_threads()

    def _settings_set_threads(self):
        if not hasattr(self, '_thread_frame'):
            self._thread_frame = ctk.CTkFrame(self)

            self._thread_frame_title = ctk.CTkTextbox(
                self._thread_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._thread_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._thread_frame_title.insert('end', self._locales.get_string('set_threads_title'))
            self._thread_frame_title.configure(state='disabled')
            self._current_threads = ctk.CTkLabel(
                self._thread_frame,
                text=f'{self._locales.get_string("current_threads")}: {self._settings.get_setting("threads")}'
            )
            self._input_threads_frame = ctk.CTkFrame(self._thread_frame, fg_color=self._thread_frame.cget('fg_color'))

            def _input_validator(x):
                if (x.isdigit() and 0 < int(x) < 1000) or x == '':
                    self._apply_threads_button.configure(state='normal')
                    return True

                return False

            self._thread_input = ctk.CTkEntry(
                self._input_threads_frame,
                validate='key',
                validatecommand=(self.register(_input_validator), '%P'),
            )
            self._thread_new_threads_title = ctk.CTkLabel(self._input_threads_frame, text=self._locales.get_string('new_threads'))

            def _set_threads():
                threads = self._thread_input.get()

                if threads == '':
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('no_value_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

                    return

                self._settings.change_setting('threads', threads)
                self._thread_input.delete(0, 'end')
                self._apply_threads_button.configure(state='disabled')
                self._current_threads.configure(text=f'{self._locales.get_string("current_threads")}: {self._settings.get_setting("threads")}')

            def _cancel():
                self._thread_input.delete(0, 'end')
                self._apply_threads_button.configure(state='disabled')

            self._confirm_threads_frame = ctk.CTkFrame(self._thread_frame, fg_color=self._thread_frame.cget('fg_color'))
            self._apply_threads_button = ctk.CTkButton(
                self._confirm_threads_frame,
                text=self._locales.get_string('apply'),
                state='disabled',
                command=_set_threads
            )
            self._cancel_threads_button = ctk.CTkButton(
                self._confirm_threads_frame,
                text=self._locales.get_string('cancel'),
                command=_cancel
            )

            self._thread_frame.grid_columnconfigure(0, weight=1)
            self._thread_frame.grid_rowconfigure(3, weight=1)

            self._thread_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._current_threads.grid(row=1, column=0, sticky='w', padx=5)
            self._input_threads_frame.grid(row=2, column=0, sticky='w')
            self._thread_new_threads_title.grid(row=0, column=0, sticky='w', padx=5, pady=(5, 0))
            self._thread_input.grid(row=0, column=1, sticky='w', padx=5, pady=5)
            self._apply_threads_button.grid(row=0, column=0, padx=5, pady=5)
            self._cancel_threads_button.grid(row=0, column=1, padx=5, pady=5)
            self._confirm_threads_frame.grid(row=3, column=0, sticky='se', padx=5, pady=5)

        if self._current_frame is not None:
            self._current_frame.grid_forget()

        self._thread_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._thread_frame
        return

    def _settings_set_path(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Смена папки, в которой производится синхронизация треков")}\n\n'
                  f'{Utils.green("Текущее расположение:")} {"Не задано" if (directory := self._settings.get_setting("path_for_sync")) == "" else directory}')

            print(f'{Utils.blue("[1]")} - Поменять расположение\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    try:
                        directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                        self._settings.change_setting('path_for_sync', directory)

                        print(f'{Utils.green("Путь изменен на:")} {directory}')
                        time.sleep(1)

                    except Exception:
                        print(Utils.red('Отменено'))
                        time.sleep(1)

                    break

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def _settings_set_auto_compare(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Автоматическое обнаружение отсутствующих треков на сервере")}\n\n'
                  f'{Utils.green("Текущее значение:")} {"Включено" if self._settings.get_setting("auto_comp") == "True" else "Выключено"}')

            print(f'{Utils.blue("[1]")} - {"Выключить" if self._settings.get_setting("auto_comp") == "True" else "Включить"}\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    if self._settings.get_setting("auto_comp") == "True":
                        self._settings.change_setting('auto_comp', 'False')
                        print(Utils.green('Выключено'))
                    else:
                        self._settings.change_setting('auto_comp', 'True')
                        print(Utils.green('Включено'))

                    time.sleep(1)
                    break

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def _settings_clear_login_data(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Очистка данных для входа в аккаунт")}\n\n'
                  f'{Utils.blue("[1]")} - Очистить\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    self._settings.change_setting('client_id', '')
                    self._settings.change_setting('client_secret', '')
                    self._settings.change_setting('redirect_uri', '')
                    self._settings.change_setting('code', '')

                    try:
                        os.remove(self._settings.get_path() + '\\.cache')
                    except FileNotFoundError:
                        pass

                    print(Utils.green('Очищено'))
                    time.sleep(1)
                    break

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def _settings_local_ignore_list(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Управление локальным игнор листом")}\n'
                  f'{Utils.green("Эти треки будут игнорироваться при получении треков из spotify")}\n')

            print(f'{Utils.blue("[1]")} - Вывести текущий список треков\n'
                  f'{Utils.blue("[2]")} - Добавить трек в игнор лист\n'
                  f'{Utils.blue("[3]")} - Удалить трек из игнор листа\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    for i, name in enumerate(il := sorted(self._settings.get_all_local_ignore_tracks())):
                        print(f'{i + 1}) "{name}"')

                    if len(il) == 0:
                        print(Utils.yellow('Список пуст'))

                case '2':
                    print(Utils.yellow('Введи название трека\n\n'
                                       f'{Utils.purple("[b]")} - Назад'))

                    name = Utils.g_input('> ')

                    if name == 'b':
                        print(Utils.green('Отмена ввода'))
                        continue

                    try:
                        self._settings.add_track_to_local_ignore(name)

                        self._settings.save()

                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} добавлен в игнор лист{Utils.Colors.END}')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} уже был добавлен игнор лист{Utils.Colors.END}')

                case '3':
                    Utils.remove_tracks_from_ignore(sorted(self._settings.get_all_local_ignore_tracks()), self._settings.delete_track_from_local_ignore)

                    self._settings.save()

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def _settings_server_ignore_list(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Управление серверным игнор листом")}\n'
                  f'{Utils.green("Эти треки будут игнорироваться при поиске треков, которых нет в spotify")}\n')

            print(f'{Utils.blue("[1]")} - Вывести текущий список треков\n'
                  f'{Utils.blue("[2]")} - Добавить трек в игнор лист\n'
                  f'{Utils.blue("[3]")} - Удалить трек из игнор листа\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    for i, name in enumerate(il := sorted(self._settings.get_all_server_ignore_tracks())):
                        print(f'{i + 1}) "{name}"')

                    if len(il) == 0:
                        print(Utils.yellow('Список пуст'))

                case '2':
                    print(Utils.yellow('Введи название трека\n\n'
                                       f'{Utils.purple("[b]")} - Назад'))

                    name = Utils.g_input('> ')

                    if name == 'b':
                        print(Utils.green('Отмена ввода'))
                        continue

                    try:
                        self._settings.add_track_to_server_ignore(name)

                        self._settings.save()

                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} добавлен в игнор лист{Utils.Colors.END}')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} уже был добавлен игнор лист{Utils.Colors.END}')

                case '3':
                    Utils.remove_tracks_from_ignore(sorted(self._settings.get_all_server_ignore_tracks()), self._settings.delete_track_from_server_ignore)

                    self._settings.save()

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def _settings_auto_update(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Автоматическая проверка обновлений")}\n\n'
                  f'{Utils.green("Текущее значение:")} {"Включено" if self._settings.get_setting("auto_update") == "True" else "Выключено"}')

            print(f'{Utils.blue("[1]")} - {"Выключить" if self._settings.get_setting("auto_update") == "True" else "Включить"}\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    if self._settings.get_setting("auto_update") == "True":
                        self._settings.change_setting('auto_update', 'False')
                        print(Utils.green('Выключено'))
                    else:
                        self._settings.change_setting('auto_update', 'True')
                        print(Utils.green('Включено'))

                    time.sleep(1)
                    break

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def _settings_overwrite_tracks(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Перезапись существующих треков при загрузке")}\n\n'
                  f'{Utils.green("Текущее значение:")} {"Включено" if self._settings.get_setting("overwrite_tracks") == "True" else "Выключено"}')

            print(f'{Utils.blue("[1]")} - {"Выключить" if self._settings.get_setting("overwrite_tracks") == "True" else "Включить"}\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    if self._settings.get_setting("overwrite_tracks") == "True":
                        self._settings.change_setting('overwrite_tracks', 'False')
                        print(Utils.green('Выключено'))
                    else:
                        self._settings.change_setting('overwrite_tracks', 'True')
                        print(Utils.green('Включено'))

                    time.sleep(1)
                    break

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))
