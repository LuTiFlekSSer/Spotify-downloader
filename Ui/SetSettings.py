import SettingsStorage
import os
import win32com.client
import Utils
import customtkinter as ctk
import Locales
from PIL import Image
from CTkMessagebox import CTkMessagebox
import pyperclip
from CustomTable import CustomTable


class SetSettings(ctk.CTkFrame):
    def __init__(self, master, callback):
        super().__init__(master)

        self._new_directory = None
        self._locales = Locales.Locales()
        self._settings = SettingsStorage.Settings()
        self._table_limit = 20
        self._local_ignore_table_data = None
        self._server_ignore_table_data = None

        self._buttons_container = ctk.CTkScrollableFrame(self, width=220)
        self._title_frame = ctk.CTkFrame(self)

        self._back_image = ctk.CTkImage(Image.open(Utils.resource_path('icons/back.png')), size=(20, 20))

        def _callback():
            self._settings_set_threads()
            callback()

        self._back_button = ctk.CTkButton(
            self._title_frame,
            image=self._back_image,
            command=_callback,
            text='',
            width=20,
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
        )
        self._settings_title = ctk.CTkLabel(
            self._title_frame,
            text=self._locales.get_string('settings'),
            font=('Arial', 23, 'bold')
        )

        self._set_threads_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('set_threads'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_set_threads
        )
        self._set_sync_dir_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('set_sync_dir'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_set_path
        )
        self._set_auto_compare_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('set_auto_tracks_compare'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_set_auto_compare
        )
        self._clear_data_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('clear_data'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_clear_login_data
        )
        self._local_ignore_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('local_ignore'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_local_ignore_list
        )
        self._server_ignore_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('server_ignore'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_server_ignore_list
        )
        self._update_check_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('auto_check_update'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_auto_update
        )
        self._rewrite_tracks_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('rewrite_tracks'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_overwrite_tracks
        )
        self._set_language_button = ctk.CTkButton(
            self._buttons_container,
            text=self._locales.get_string('language'),
            hover_color=("gray70", "gray30"),
            fg_color="transparent",
            corner_radius=0,
            border_spacing=10,
            anchor='w',
            command=self._settings_set_language
        )

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._title_frame.grid_columnconfigure(0, weight=1)
        self._title_frame.grid_rowconfigure(0, weight=1)
        self._buttons_container.grid_columnconfigure(0, weight=1)

        self._settings_title.grid(row=0, column=0, sticky='ns')
        self._back_button.grid(row=0, column=0, sticky='w', padx=2)
        self._title_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe', columnspan=2, ipady=4)

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
        self._current_button = None
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
                text=f'{self._locales.get_string("current_threads")} {self._settings.get_setting("threads")}'
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
                self._current_threads.configure(text=f'{self._locales.get_string("current_threads")} {self._settings.get_setting("threads")}')

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

        if self._current_button is not None:
            self._current_button.configure(fg_color='transparent')

        self._set_threads_button.configure(fg_color=('gray75', 'gray25'))
        self._thread_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._thread_frame
        self._current_button = self._set_threads_button
        return

    def _settings_set_path(self):
        if not hasattr(self, '_path_frame'):
            self._path_frame = ctk.CTkFrame(self)

            self._path_frame_title = ctk.CTkTextbox(
                self._path_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._path_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._path_frame_title.insert('end', self._locales.get_string('set_path_title'))
            self._path_frame_title.configure(state='disabled')

            self._current_path_frame = ctk.CTkFrame(self._path_frame, fg_color=self._path_frame.cget('fg_color'))
            self._current_path_title = ctk.CTkLabel(
                self._current_path_frame,
                text=f'{self._locales.get_string("current_path")}',
            )
            self._current_path = ctk.CTkTextbox(
                self._current_path_frame,
                height=25,
                fg_color=self._thread_frame.cget('fg_color'),
                wrap='none'
            )

            def _get_current_path():
                if (curr_path := self._settings.get_setting("path_for_sync")) != '':
                    return f'"{curr_path}"'
                else:
                    return self._locales.get_string("not_specified")

            self._current_path.insert('end', f'{_get_current_path()}')
            self._current_path.configure(state='disabled')

            self._new_path_frame = ctk.CTkFrame(self._path_frame, fg_color=self._path_frame.cget('fg_color'))
            self._new_path_title = ctk.CTkLabel(
                self._new_path_frame,
                text=f'{self._locales.get_string("new_path")}'
            )
            self._new_path = ctk.CTkTextbox(
                self._new_path_frame,
                height=25,
                fg_color=self._thread_frame.cget('fg_color'),
                wrap='none'
            )
            self._new_path.insert('end', f'{self._locales.get_string("not_specified")}')
            self._new_path.configure(state='disabled')

            def _select_path():
                try:
                    self._new_directory = (win32com.client.Dispatch('Shell.Application').
                                           BrowseForFolder(0, self._locales.get_string('choose_folder'), 16, "").Self.path)

                    self._new_path.configure(state='normal')
                    self._new_path.delete('0.0', 'end')
                    self._new_path.insert('end', f'"{self._new_directory}"')
                    self._new_path.configure(state='disabled')

                    self._apply_path_button.configure(state='normal')
                except Exception:
                    pass

            self._input_path_button = ctk.CTkButton(
                self._path_frame,
                text=self._locales.get_string('input_path'),
                command=_select_path
            )

            def _set_path():
                self._settings.change_setting('path_for_sync', self._new_directory)

                self._new_path.configure(state='normal')
                self._new_path.delete('0.0', 'end')
                self._new_path.insert('end', f'{self._locales.get_string("not_specified")}')
                self._new_path.configure(state='disabled')

                self._apply_path_button.configure(state='disabled')

                self._current_path.configure(state='normal')
                self._current_path.delete('0.0', 'end')
                self._current_path.insert('end', f'{_get_current_path()}')
                self._current_path.configure(state='disabled')

            def _cancel():
                self._new_path.configure(state='normal')
                self._new_path.delete('0.0', 'end')
                self._new_path.insert('end', f'{self._locales.get_string("not_specified")}')
                self._new_path.configure(state='disabled')

                self._apply_path_button.configure(state='disabled')

            self._confirm_path_frame = ctk.CTkFrame(self._path_frame, fg_color=self._path_frame.cget('fg_color'))
            self._apply_path_button = ctk.CTkButton(
                self._confirm_path_frame,
                text=self._locales.get_string('apply'),
                state='disabled',
                command=_set_path
            )
            self._cancel_path_button = ctk.CTkButton(
                self._confirm_path_frame,
                text=self._locales.get_string('cancel'),
                command=_cancel
            )

            self._path_frame.grid_columnconfigure(0, weight=1)
            self._path_frame.grid_rowconfigure(4, weight=1)
            self._current_path_frame.grid_columnconfigure(1, weight=1)
            self._new_path_frame.grid_columnconfigure(1, weight=1)

            self._path_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))

            self._current_path_title.grid(row=0, column=0, sticky='w', padx=(5, 0))
            self._current_path.grid(row=0, column=1, sticky='we')
            self._current_path_frame.grid(row=1, column=0, sticky='we')

            self._new_path_title.grid(row=0, column=0, sticky='w', padx=(5, 0))
            self._new_path.grid(row=0, column=1, sticky='we')
            self._new_path_frame.grid(row=2, column=0, sticky='we')

            self._input_path_button.grid(row=3, column=0, sticky='w', padx=5, pady=5)
            self._apply_path_button.grid(row=0, column=0, padx=5, pady=5)
            self._cancel_path_button.grid(row=0, column=1, padx=5, pady=5)
            self._confirm_path_frame.grid(row=4, column=0, sticky='se', padx=5, pady=5)

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._set_sync_dir_button.configure(fg_color=('gray75', 'gray25'))
        self._path_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._path_frame
        self._current_button = self._set_sync_dir_button

    def _settings_set_auto_compare(self):
        if not hasattr(self, '_auto_compare_frame'):
            self._auto_compare_frame = ctk.CTkFrame(self)

            self._auto_compare_frame_title = ctk.CTkTextbox(
                self._auto_compare_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._auto_compare_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._auto_compare_frame_title.insert('end', self._locales.get_string('set_auto_compare_title'))
            self._auto_compare_frame_title.configure(state='disabled')

            curr_value = 0 if self._settings.get_setting('auto_comp') == 'True' else 1

            def _radio_command():
                self._apply_auto_compare_button.configure(state='normal')

            self._auto_compare_var = ctk.IntVar(self, curr_value)
            self._auto_compare_on_radio = ctk.CTkRadioButton(
                self._auto_compare_frame,
                text=self._locales.get_string('on'),
                variable=self._auto_compare_var,
                value=0,
                command=_radio_command
            )
            self._auto_compare_off_radio = ctk.CTkRadioButton(
                self._auto_compare_frame,
                text=self._locales.get_string('off'),
                variable=self._auto_compare_var,
                value=1,
                command=_radio_command
            )

            def _set_auto_compare():
                self._settings.change_setting('auto_comp', 'True' if self._auto_compare_var.get() == 0 else 'False')
                self._apply_auto_compare_button.configure(state='disabled')

            def _cancel():
                self._auto_compare_var.set(0 if self._settings.get_setting('auto_comp') == 'True' else 1)
                self._apply_auto_compare_button.configure(state='disabled')

            self._confirm_auto_compare_frame = ctk.CTkFrame(self._auto_compare_frame, fg_color=self._auto_compare_frame.cget('fg_color'))
            self._apply_auto_compare_button = ctk.CTkButton(
                self._confirm_auto_compare_frame,
                text=self._locales.get_string('apply'),
                command=_set_auto_compare,
                state='disabled'
            )
            self._cancel_auto_compare_button = ctk.CTkButton(
                self._confirm_auto_compare_frame,
                text=self._locales.get_string('cancel'),
                command=_cancel
            )

            self._auto_compare_frame.grid_columnconfigure(0, weight=1)
            self._auto_compare_frame.grid_rowconfigure(3, weight=1)

            self._auto_compare_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._auto_compare_on_radio.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self._auto_compare_off_radio.grid(row=2, column=0, sticky='w', padx=5, pady=5)
            self._apply_auto_compare_button.grid(row=0, column=0, padx=5, pady=5)
            self._cancel_auto_compare_button.grid(row=0, column=1, padx=5, pady=5)
            self._confirm_auto_compare_frame.grid(row=3, column=0, sticky='se', padx=5, pady=5)

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._set_auto_compare_button.configure(fg_color=('gray75', 'gray25'))
        self._auto_compare_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._auto_compare_frame
        self._current_button = self._set_auto_compare_button

    def _settings_clear_login_data(self):
        if not hasattr(self, '_clear_login_frame'):
            self._clear_login_frame = ctk.CTkFrame(self)

            self._clear_login_frame_title = ctk.CTkTextbox(
                self._clear_login_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._clear_login_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._clear_login_frame_title.insert('end', self._locales.get_string('clear_login_data_title'))
            self._clear_login_frame_title.configure(state='disabled')

            def _clear_login_data():
                result = CTkMessagebox(
                    title=self._locales.get_string('clear?'),
                    message=self._locales.get_string('clear_login_data'),
                    icon='question',
                    option_1=self._locales.get_string('yes'),
                    option_2=self._locales.get_string('no'),
                    topmost=False
                ).get()

                if result == self._locales.get_string('yes'):
                    self._settings.change_setting('client_id', '')
                    self._settings.change_setting('client_secret', '')
                    self._settings.change_setting('redirect_uri', '')
                    self._settings.change_setting('code', '')

                    try:
                        os.remove(self._settings.get_path() + '\\.cache')
                    except FileNotFoundError:
                        pass

                    CTkMessagebox(
                        title=self._locales.get_string('clear_title'),
                        message=self._locales.get_string('data_cleared'),
                        icon='check',
                        topmost=False
                    ).get()

            self._clear_login_data_button = ctk.CTkButton(
                self._clear_login_frame,
                text=self._locales.get_string('clear'),
                command=_clear_login_data
            )

            self._clear_login_frame.grid_columnconfigure(0, weight=1)

            self._clear_login_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._clear_login_data_button.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._clear_data_button.configure(fg_color=('gray75', 'gray25'))
        self._clear_login_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._clear_login_frame
        self._current_button = self._clear_data_button

    def _settings_local_ignore_list(self):
        def _create_values_for_table(values, offset=0):
            return [['№', self._locales.get_string('title')]] + [[offset + i + 1, track] for i, track in enumerate(values)]

        def _update_table(values):
            self._local_ignore_table_data = values
            rows_count = len(self._local_ignore_table.get())

            was_updated = False
            tmp_values = []

            for i, value in enumerate(_create_values_for_table(self._local_ignore_table_data[:self._table_limit])):
                if i < rows_count:
                    tmp_values.append(value)
                else:
                    if not was_updated:
                        was_updated = True
                        self._local_ignore_table.update_values(tmp_values)

                    self._local_ignore_table.add_row(value, width=10)

            if not was_updated:
                self._local_ignore_table.update_values(tmp_values)

            if len(self._local_ignore_table_data) > self._table_limit:
                self._next_page_local_ignore_table.grid(row=1, column=1, sticky='e', padx=5, pady=5)
                self._previous_page_local_ignore_table.grid(row=1, column=0, sticky='w', padx=5, pady=5)

                self._next_page_local_ignore_table.configure(state='normal')
                self._previous_page_local_ignore_table.configure(state='disabled')

                self._local_table_page = 0
            else:
                self._next_page_local_ignore_table.grid_forget()
                self._previous_page_local_ignore_table.grid_forget()

                self._local_ignore_table.delete_rows([i for i in range(len(values) + 1, len(self._local_ignore_table.get()))])

        def _next_page():
            self._local_ignore_table_frame._parent_canvas.yview_moveto(0)
            self._local_table_page += 1

            self._local_ignore_table.update_values(
                _create_values_for_table(
                    self._local_ignore_table_data[self._table_limit * self._local_table_page:self._table_limit * (self._local_table_page + 1)],
                    self._table_limit * self._local_table_page
                )
            )

            self._previous_page_local_ignore_table.configure(state='normal')
            if self._table_limit * (self._local_table_page + 1) >= len(self._local_ignore_table_data):
                self._next_page_local_ignore_table.configure(state='disabled')

        def _previous_page():
            self._local_ignore_table_frame._parent_canvas.yview_moveto(0)
            self._local_table_page -= 1

            self._local_ignore_table.update_values(
                _create_values_for_table(
                    self._local_ignore_table_data[self._table_limit * self._local_table_page:self._table_limit * (self._local_table_page + 1)],
                    self._table_limit * self._local_table_page
                )
            )

            self._next_page_local_ignore_table.configure(state='normal')
            if self._local_table_page == 0:
                self._previous_page_local_ignore_table.configure(state='disabled')

        if not hasattr(self, '_local_ignore_frame'):
            self._local_ignore_frame = ctk.CTkFrame(self)

            self._local_ignore_frame_title = ctk.CTkTextbox(
                self._local_ignore_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=20,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._local_ignore_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._local_ignore_frame_title.insert('end', self._locales.get_string('local_ignore_title'))
            self._local_ignore_frame_title.configure(state='disabled')

            self._local_ignore_description = ctk.CTkTextbox(
                self._local_ignore_frame,
                wrap='word',
                height=45,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._local_ignore_description.bind('<MouseWheel>', lambda event: 'break')
            self._local_ignore_description.insert('end', self._locales.get_string('local_ignore_description'))
            self._local_ignore_description.configure(state='disabled')

            self._local_ignore_table_frame = ctk.CTkScrollableFrame(self._local_ignore_frame)

            self._local_ignore_table = CustomTable(
                self._local_ignore_table_frame,
                width=10,
                wraplength=250,
                command=lambda x: pyperclip.copy(x['value']),
                max_columns=2,
                max_rows=21
            )
            self._local_table_page = 0

            self._next_page_local_ignore_table = ctk.CTkButton(
                self._local_ignore_table_frame,
                text=self._locales.get_string('forward'),
                command=_next_page
            )
            self._previous_page_local_ignore_table = ctk.CTkButton(
                self._local_ignore_table_frame,
                text=self._locales.get_string('back'),
                command=_previous_page
            )
            _update_table(sorted(self._settings.get_all_local_ignore_tracks()))

            self._local_ignore_input_description = ctk.CTkTextbox(
                self._local_ignore_frame,
                wrap='word',
                height=45,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._local_ignore_input_description.bind('<MouseWheel>', lambda event: 'break')
            self._local_ignore_input_description.insert('end', self._locales.get_string('local_ignore_hint'))
            self._local_ignore_input_description.configure(state='disabled')

            self._local_ignore_input = ctk.CTkEntry(
                self._local_ignore_frame
            )

            self._local_ignore_button_frame = ctk.CTkFrame(
                self._local_ignore_frame,
                fg_color=self._local_ignore_frame.cget('fg_color')
            )

            def _add_track():
                track_name = self._local_ignore_input.get().strip()

                if track_name == '':
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('input_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

                    return

                try:

                    self._settings.add_track_to_local_ignore(track_name)

                    self._settings.save()

                    self._local_ignore_input.delete(0, 'end')
                    _update_table(sorted(self._settings.get_all_local_ignore_tracks()))

                except SettingsStorage.AlreadyExistsError:
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('already_exists'),
                        icon='cancel',
                        topmost=False
                    ).get()

            def _delete_tracks():
                tracks_input = self._local_ignore_input.get().strip()
                try:
                    Utils.remove_tracks_from_ignore(
                        sorted(self._settings.get_all_local_ignore_tracks()),
                        self._settings.delete_track_from_local_ignore,
                        tracks_input
                    )

                    self._settings.save()

                    self._local_ignore_input.delete(0, 'end')
                    _update_table(sorted(self._settings.get_all_local_ignore_tracks()))

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

                except SettingsStorage.NotFoundError:
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('not_found_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

            self._local_ignore_delete_button = ctk.CTkButton(
                self._local_ignore_button_frame,
                text=self._locales.get_string('delete'),
                command=_delete_tracks
            )
            self._local_ignore_add_button = ctk.CTkButton(
                self._local_ignore_button_frame,
                text=self._locales.get_string('add'),
                command=_add_track
            )

            self._local_ignore_frame.grid_columnconfigure(0, weight=1)
            self._local_ignore_frame.grid_rowconfigure(2, weight=1)
            self._local_ignore_table_frame.grid_columnconfigure((0, 1), weight=1)
            self._local_ignore_table_frame.grid_rowconfigure(0, weight=1)

            self._local_ignore_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._local_ignore_description.grid(row=1, column=0, sticky='ew', pady=(5, 0))
            self._local_ignore_table.grid(row=0, column=0, sticky='nsew', padx=5, pady=5, columnspan=2)
            self._local_ignore_table_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
            self._local_ignore_input_description.grid(row=3, column=0, sticky='ew', pady=(5, 0))
            self._local_ignore_input.grid(row=4, column=0, sticky='we', padx=5, pady=5)
            self._local_ignore_button_frame.grid(row=5, column=0, sticky='e', padx=5, pady=5)
            self._local_ignore_delete_button.grid(row=0, column=0, padx=5, pady=5)
            self._local_ignore_add_button.grid(row=0, column=1, padx=5, pady=5)

        else:
            _update_table(sorted(self._settings.get_all_local_ignore_tracks()))

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._local_ignore_button.configure(fg_color=('gray75', 'gray25'))
        self._local_ignore_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._local_ignore_frame
        self._current_button = self._local_ignore_button

    def _settings_server_ignore_list(self):
        def _create_values_for_table(values, offset=0):
            return [['№', self._locales.get_string('title')]] + [[offset + i + 1, track] for i, track in enumerate(values)]

        def _update_table(values):
            self._server_ignore_table_data = values
            rows_count = len(self._server_ignore_table.get())

            was_updated = False
            tmp_values = []

            for i, value in enumerate(_create_values_for_table(self._server_ignore_table_data[:self._table_limit])):
                if i < rows_count:
                    tmp_values.append(value)
                else:
                    if not was_updated:
                        was_updated = True
                        self._server_ignore_table.update_values(tmp_values)

                    self._server_ignore_table.add_row(value, width=10)

            if not was_updated:
                self._server_ignore_table.update_values(tmp_values)

            if len(self._server_ignore_table_data) > self._table_limit:
                self._next_page_server_ignore_table.grid(row=1, column=1, sticky='e', padx=5, pady=5)
                self._previous_page_server_ignore_table.grid(row=1, column=0, sticky='w', padx=5, pady=5)

                self._next_page_server_ignore_table.configure(state='normal')
                self._previous_page_server_ignore_table.configure(state='disabled')

                self._server_table_page = 0
            else:
                self._next_page_server_ignore_table.grid_forget()
                self._previous_page_server_ignore_table.grid_forget()

                self._server_ignore_table.delete_rows([i for i in range(len(values) + 1, len(self._server_ignore_table.get()))])

        def _next_page():
            self._server_ignore_table_frame._parent_canvas.yview_moveto(0)
            self._server_table_page += 1

            self._server_ignore_table.update_values(
                _create_values_for_table(
                    self._server_ignore_table_data[self._table_limit * self._server_table_page:self._table_limit * (self._server_table_page + 1)],
                    self._table_limit * self._server_table_page
                )
            )

            self._previous_page_server_ignore_table.configure(state='normal')
            if self._table_limit * (self._server_table_page + 1) >= len(self._server_ignore_table_data):
                self._next_page_server_ignore_table.configure(state='disabled')

        def _previous_page():
            self._server_ignore_table_frame._parent_canvas.yview_moveto(0)
            self._server_table_page -= 1

            self._server_ignore_table.update_values(
                _create_values_for_table(
                    self._server_ignore_table_data[self._table_limit * self._server_table_page:self._table_limit * (self._server_table_page + 1)],
                    self._table_limit * self._server_table_page
                )
            )

            self._next_page_server_ignore_table.configure(state='normal')
            if self._server_table_page == 0:
                self._previous_page_server_ignore_table.configure(state='disabled')

        if not hasattr(self, '_server_ignore_frame'):
            self._server_ignore_frame = ctk.CTkFrame(self)

            self._server_ignore_frame_title = ctk.CTkTextbox(
                self._server_ignore_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=20,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._server_ignore_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._server_ignore_frame_title.insert('end', self._locales.get_string('server_ignore_title'))
            self._server_ignore_frame_title.configure(state='disabled')

            self._server_ignore_description = ctk.CTkTextbox(
                self._server_ignore_frame,
                wrap='word',
                height=45,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._server_ignore_description.bind('<MouseWheel>', lambda event: 'break')
            self._server_ignore_description.insert('end', self._locales.get_string('server_ignore_description'))
            self._server_ignore_description.configure(state='disabled')

            self._server_ignore_table_frame = ctk.CTkScrollableFrame(self._server_ignore_frame)

            self._server_ignore_table = CustomTable(
                self._server_ignore_table_frame,
                width=10,
                wraplength=250,
                command=lambda x: pyperclip.copy(x['value']),
                max_columns=2,
                max_rows=21
            )
            self._server_table_page = 0

            self._next_page_server_ignore_table = ctk.CTkButton(
                self._server_ignore_table_frame,
                text=self._locales.get_string('forward'),
                command=_next_page
            )
            self._previous_page_server_ignore_table = ctk.CTkButton(
                self._server_ignore_table_frame,
                text=self._locales.get_string('back'),
                command=_previous_page
            )
            _update_table(sorted(self._settings.get_all_server_ignore_tracks()))

            self._server_ignore_input_description = ctk.CTkTextbox(
                self._server_ignore_frame,
                wrap='word',
                height=45,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._server_ignore_input_description.bind('<MouseWheel>', lambda event: 'break')
            self._server_ignore_input_description.insert('end', self._locales.get_string('local_ignore_hint'))
            self._server_ignore_input_description.configure(state='disabled')

            self._server_ignore_input = ctk.CTkEntry(
                self._server_ignore_frame
            )

            self._server_ignore_button_frame = ctk.CTkFrame(
                self._server_ignore_frame,
                fg_color=self._server_ignore_frame.cget('fg_color')
            )

            def _add_track():
                track_name = self._server_ignore_input.get().strip()

                if track_name == '':
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('input_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

                    return

                try:

                    self._settings.add_track_to_server_ignore(track_name)

                    self._settings.save()

                    self._server_ignore_input.delete(0, 'end')
                    _update_table(sorted(self._settings.get_all_server_ignore_tracks()))

                except SettingsStorage.AlreadyExistsError:
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('already_exists'),
                        icon='cancel',
                        topmost=False
                    ).get()

            def _delete_tracks():
                tracks_input = self._server_ignore_input.get().strip()
                try:
                    Utils.remove_tracks_from_ignore(
                        sorted(self._settings.get_all_server_ignore_tracks()),
                        self._settings.delete_track_from_server_ignore,
                        tracks_input
                    )

                    self._settings.save()

                    self._server_ignore_input.delete(0, 'end')
                    _update_table(sorted(self._settings.get_all_server_ignore_tracks()))

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

                except SettingsStorage.NotFoundError:
                    CTkMessagebox(
                        title=self._locales.get_string('error'),
                        message=self._locales.get_string('not_found_error'),
                        icon='cancel',
                        topmost=False
                    ).get()

            self._server_ignore_delete_button = ctk.CTkButton(
                self._server_ignore_button_frame,
                text=self._locales.get_string('delete'),
                command=_delete_tracks
            )
            self._server_ignore_add_button = ctk.CTkButton(
                self._server_ignore_button_frame,
                text=self._locales.get_string('add'),
                command=_add_track
            )

            self._server_ignore_frame.grid_columnconfigure(0, weight=1)
            self._server_ignore_frame.grid_rowconfigure(2, weight=1)
            self._server_ignore_table_frame.grid_columnconfigure((0, 1), weight=1)
            self._server_ignore_table_frame.grid_rowconfigure(0, weight=1)

            self._server_ignore_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._server_ignore_description.grid(row=1, column=0, sticky='ew', pady=(5, 0))
            self._server_ignore_table.grid(row=0, column=0, sticky='nsew', padx=5, pady=5, columnspan=2)
            self._server_ignore_table_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
            self._server_ignore_input_description.grid(row=3, column=0, sticky='ew', pady=(5, 0))
            self._server_ignore_input.grid(row=4, column=0, sticky='we', padx=5, pady=5)
            self._server_ignore_button_frame.grid(row=5, column=0, sticky='e', padx=5, pady=5)
            self._server_ignore_delete_button.grid(row=0, column=0, padx=5, pady=5)
            self._server_ignore_add_button.grid(row=0, column=1, padx=5, pady=5)

        else:
            _update_table(sorted(self._settings.get_all_server_ignore_tracks()))

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._server_ignore_button.configure(fg_color=('gray75', 'gray25'))
        self._server_ignore_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._server_ignore_frame
        self._current_button = self._server_ignore_button

    def _settings_auto_update(self):
        if not hasattr(self, '_auto_update_frame'):
            self._auto_update_frame = ctk.CTkFrame(self)

            self._auto_update_frame_title = ctk.CTkTextbox(
                self._auto_update_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._auto_update_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._auto_update_frame_title.insert('end', self._locales.get_string('set_auto_update_title'))
            self._auto_update_frame_title.configure(state='disabled')

            curr_value = 0 if self._settings.get_setting('auto_update') == 'True' else 1

            def _radio_command():
                self._apply_auto_update_button.configure(state='normal')

            self._auto_update_var = ctk.IntVar(self, curr_value)
            self._auto_update_on_radio = ctk.CTkRadioButton(
                self._auto_update_frame,
                text=self._locales.get_string('on'),
                variable=self._auto_update_var,
                value=0,
                command=_radio_command
            )
            self._auto_update_off_radio = ctk.CTkRadioButton(
                self._auto_update_frame,
                text=self._locales.get_string('off'),
                variable=self._auto_update_var,
                value=1,
                command=_radio_command
            )

            def _set_auto_update():
                self._settings.change_setting('auto_update', 'True' if self._auto_update_var.get() == 0 else 'False')
                self._apply_auto_update_button.configure(state='disabled')

            def _cancel():
                self._auto_update_var.set(0 if self._settings.get_setting('auto_update') == 'True' else 1)
                self._apply_auto_update_button.configure(state='disabled')

            self._confirm_auto_update_frame = ctk.CTkFrame(self._auto_update_frame, fg_color=self._auto_update_frame.cget('fg_color'))
            self._apply_auto_update_button = ctk.CTkButton(
                self._confirm_auto_update_frame,
                text=self._locales.get_string('apply'),
                command=_set_auto_update,
                state='disabled'
            )
            self._cancel_auto_update_button = ctk.CTkButton(
                self._confirm_auto_update_frame,
                text=self._locales.get_string('cancel'),
                command=_cancel
            )

            self._auto_update_frame.grid_columnconfigure(0, weight=1)
            self._auto_update_frame.grid_rowconfigure(3, weight=1)

            self._auto_update_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._auto_update_on_radio.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self._auto_update_off_radio.grid(row=2, column=0, sticky='w', padx=5, pady=5)
            self._apply_auto_update_button.grid(row=0, column=0, padx=5, pady=5)
            self._cancel_auto_update_button.grid(row=0, column=1, padx=5, pady=5)
            self._confirm_auto_update_frame.grid(row=3, column=0, sticky='se', padx=5, pady=5)

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._update_check_button.configure(fg_color=('gray75', 'gray25'))
        self._auto_update_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._auto_update_frame
        self._current_button = self._update_check_button

    def _settings_overwrite_tracks(self):
        if not hasattr(self, '_overwrite_tracks_frame'):
            self._overwrite_tracks_frame = ctk.CTkFrame(self)

            self._overwrite_tracks_frame_title = ctk.CTkTextbox(
                self._overwrite_tracks_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._overwrite_tracks_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._overwrite_tracks_frame_title.insert('end', self._locales.get_string('set_overwrite_tracks_title'))
            self._overwrite_tracks_frame_title.configure(state='disabled')

            curr_value = 0 if self._settings.get_setting('overwrite_tracks') == 'True' else 1

            def _radio_command():
                self._apply_overwrite_tracks_button.configure(state='normal')

            self._overwrite_tracks_var = ctk.IntVar(self, curr_value)
            self._overwrite_tracks_on_radio = ctk.CTkRadioButton(
                self._overwrite_tracks_frame,
                text=self._locales.get_string('on'),
                variable=self._overwrite_tracks_var,
                value=0,
                command=_radio_command
            )
            self._overwrite_tracks_off_radio = ctk.CTkRadioButton(
                self._overwrite_tracks_frame,
                text=self._locales.get_string('off'),
                variable=self._overwrite_tracks_var,
                value=1,
                command=_radio_command
            )

            def _set_overwrite_tracks():
                self._settings.change_setting('overwrite_tracks', 'True' if self._overwrite_tracks_var.get() == 0 else 'False')
                self._apply_overwrite_tracks_button.configure(state='disabled')

            def _cancel():
                self._overwrite_tracks_var.set(0 if self._settings.get_setting('overwrite_tracks') == 'True' else 1)
                self._apply_overwrite_tracks_button.configure(state='disabled')

            self._confirm_overwrite_tracks_frame = ctk.CTkFrame(self._overwrite_tracks_frame, fg_color=self._overwrite_tracks_frame.cget('fg_color'))
            self._apply_overwrite_tracks_button = ctk.CTkButton(
                self._confirm_overwrite_tracks_frame,
                text=self._locales.get_string('apply'),
                command=_set_overwrite_tracks,
                state='disabled'
            )
            self._cancel_overwrite_tracks_button = ctk.CTkButton(
                self._confirm_overwrite_tracks_frame,
                text=self._locales.get_string('cancel'),
                command=_cancel
            )

            self._overwrite_tracks_frame.grid_columnconfigure(0, weight=1)
            self._overwrite_tracks_frame.grid_rowconfigure(3, weight=1)

            self._overwrite_tracks_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._overwrite_tracks_on_radio.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self._overwrite_tracks_off_radio.grid(row=2, column=0, sticky='w', padx=5, pady=5)
            self._apply_overwrite_tracks_button.grid(row=0, column=0, padx=5, pady=5)
            self._cancel_overwrite_tracks_button.grid(row=0, column=1, padx=5, pady=5)
            self._confirm_overwrite_tracks_frame.grid(row=3, column=0, sticky='se', padx=5, pady=5)

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._rewrite_tracks_button.configure(fg_color=('gray75', 'gray25'))
        self._overwrite_tracks_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._overwrite_tracks_frame
        self._current_button = self._rewrite_tracks_button

    def _settings_set_language(self):
        if not hasattr(self, '_set_language_frame'):
            self._set_language_frame = ctk.CTkFrame(self)

            self._language_frame_title = ctk.CTkTextbox(
                self._set_language_frame,
                font=('Arial', 17, 'bold'),
                wrap='word',
                height=51,
                activate_scrollbars=False,
                padx=0,
                pady=0,
                fg_color=self._thread_frame.cget('fg_color')
            )
            self._language_frame_title.bind('<MouseWheel>', lambda event: 'break')
            self._language_frame_title.insert('end', self._locales.get_string('set_language_title'))
            self._language_frame_title.configure(state='disabled')

            def _language_list_callback(choice):
                self._apply_language_button.configure(state='normal')

            self._language_list = ctk.CTkComboBox(
                self._set_language_frame,
                values=list(self._locales.get_languages().values()),
                command=_language_list_callback,
                state='readonly'
            )
            self._language_list.set(self._locales.get_languages()[self._settings.get_setting('language')])

            def _set_language():
                language = self._language_list.get()

                for code, lang in self._locales.get_languages().items():
                    if lang == language:
                        language = code
                        break

                self._settings.change_setting('language', language)
                self._apply_language_button.configure(state='disabled')

                CTkMessagebox(
                    title=self._locales.get_string('language_changed'),
                    message=self._locales.get_string('language_changed_message'),
                    icon='info',
                    topmost=False
                ).get()

            def _cancel():
                self._language_list.set(self._locales.get_languages()[self._settings.get_setting('language')])
                self._apply_language_button.configure(state='disabled')

            self._confirm_language_frame = ctk.CTkFrame(self._set_language_frame, fg_color=self._set_language_frame.cget('fg_color'))
            self._apply_language_button = ctk.CTkButton(
                self._confirm_language_frame,
                text=self._locales.get_string('apply'),
                command=_set_language,
                state='disabled'
            )
            self._cancel_language_button = ctk.CTkButton(
                self._confirm_language_frame,
                text=self._locales.get_string('cancel'),
                command=_cancel
            )

            self._set_language_frame.grid_columnconfigure(0, weight=1)
            self._set_language_frame.grid_rowconfigure(2, weight=1)

            self._language_frame_title.grid(row=0, column=0, sticky='ew', pady=(5, 0))
            self._language_list.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            self._apply_language_button.grid(row=0, column=0, padx=5, pady=5)
            self._cancel_language_button.grid(row=0, column=1, padx=5, pady=5)
            self._confirm_language_frame.grid(row=2, column=0, sticky='se', padx=5, pady=5)

        self._current_frame.grid_forget()
        self._current_button.configure(fg_color='transparent')

        self._set_language_button.configure(fg_color=('gray75', 'gray25'))
        self._set_language_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        self._current_frame = self._set_language_frame
        self._current_button = self._set_language_button
