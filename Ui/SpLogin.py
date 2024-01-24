import SettingsStorage
import SpotifyLogin
import pyperclip
import customtkinter as ctk
import Locales
from CTkMessagebox import CTkMessagebox
import webbrowser


class SpLogin(ctk.CTkFrame):
    def __init__(self, master, callback):
        super().__init__(master)

        self._settings = SettingsStorage.Settings()
        self._locales = Locales.Locales()

        self._login_title = ctk.CTkLabel(
            self,
            text=self._locales.get_string('login_title'),
            font=('Arial', 18, 'bold'),
        )

        self._input_data_frame = ctk.CTkFrame(
            self,
            fg_color=self.cget('fg_color')
        )

        self._client_id_title = ctk.CTkLabel(
            self._input_data_frame,
            text='Client ID:',
        )
        self._client_id_entry = ctk.CTkEntry(
            self._input_data_frame,
        )

        self._client_secret_title = ctk.CTkLabel(
            self._input_data_frame,
            text='Client secret:',
        )
        self._client_secret_entry = ctk.CTkEntry(
            self._input_data_frame,
        )

        self._redirect_uri_title = ctk.CTkLabel(
            self._input_data_frame,
            text='Redirect URI:',
        )
        self._redirect_uri_entry = ctk.CTkEntry(
            self._input_data_frame,
        )

        self._button_frame = ctk.CTkFrame(
            self,
            fg_color=self.cget('fg_color')
        )

        self._input_code_frame = ctk.CTkFrame(
            self,
            fg_color=self.cget('fg_color')
        )

        self._code_description = ctk.CTkTextbox(
            self._input_code_frame,
            wrap='word',
            height=45,
            activate_scrollbars=False,
            padx=0,
            pady=0,
            fg_color=self.cget('fg_color')
        )
        self._code_description.bind('<MouseWheel>', lambda event: 'break')
        self._code_description.insert('end', self._locales.get_string('code_description'))
        self._code_description.configure(state='disabled')

        self._link = ctk.CTkTextbox(
            self._input_code_frame,
            height=90,
            activate_scrollbars=False,
            padx=0,
            pady=0,
            fg_color=self.cget('fg_color'),
            text_color='#5b97fe',
            cursor='hand2',
        )
        self._link.bind('<MouseWheel>', lambda event: 'break')
        self._link.configure(state='disabled')

        self._code_title = ctk.CTkLabel(
            self._input_code_frame,
            text='URL:',
        )
        self._code_input_entry = ctk.CTkEntry(
            self._input_code_frame,
        )

        def _link_configure(link):
            self._link.configure(state='normal')

            self._link.delete('0.0', 'end')
            self._link.insert('end', link)

            self._link.configure(state='disabled')

            self._link.unbind('<Button-1>')
            self._link.bind('<Button-1>', lambda event: webbrowser.open_new(link))

        frame_state = 0

        def _next_command():
            nonlocal frame_state

            match frame_state:
                case 0:
                    client_id = self._client_id_entry.get().strip()
                    client_secret = self._client_secret_entry.get().strip()
                    redirect_uri = self._redirect_uri_entry.get().strip()

                    try:
                        spl = SpotifyLogin.Login(client_id, client_secret, redirect_uri)
                    except SpotifyLogin.LoginDataError:
                        CTkMessagebox(
                            title=self._locales.get_string('error'),
                            message=self._locales.get_string('login_error'),
                            icon='cancel',
                            topmost=False
                        ).get()

                        return

                    a_url = spl.get_authorization_url()
                    pyperclip.copy(a_url)

                    _link_configure(a_url)

                    self._back_button.grid(row=0, column=0, sticky='e', padx=5, pady=5)
                    self._input_data_frame.grid_forget()
                    self._input_code_frame.grid(row=1, column=0, sticky='nsew')

                    frame_state = 1

                case 1:
                    client_id = self._client_id_entry.get().strip()
                    client_secret = self._client_secret_entry.get().strip()
                    redirect_uri = self._redirect_uri_entry.get().strip()
                    code = self._code_input_entry.get().strip()

                    spl = SpotifyLogin.Login(client_id, client_secret, redirect_uri)

                    try:
                        spl.login_with_authorization_code(code)

                        self._settings.change_setting('client_id', client_id)
                        self._settings.change_setting('client_secret', client_secret)
                        self._settings.change_setting('redirect_uri', redirect_uri)

                        self._settings.change_setting('code', code)

                        _back_command()

                        self._client_id_entry.delete('0', 'end')
                        self._client_secret_entry.delete('0', 'end')
                        self._redirect_uri_entry.delete('0', 'end')

                        callback()

                    except SpotifyLogin.AuthorizationUrlError:
                        CTkMessagebox(
                            title=self._locales.get_string('error'),
                            message=self._locales.get_string('url_code_error'),
                            icon='cancel',
                            topmost=False
                        ).get()

                    except SpotifyLogin.AuthorizationError:
                        CTkMessagebox(
                            title=self._locales.get_string('error'),
                            message=self._locales.get_string('authorization_error'),
                            icon='cancel',
                            topmost=False
                        ).get()

        def _back_command():
            nonlocal frame_state

            match frame_state:
                case 1:
                    self._back_button.grid_forget()
                    self._input_code_frame.grid_forget()
                    self._input_data_frame.grid(row=1, column=0, sticky='nsew')

                    frame_state = 0

        self._back_button = ctk.CTkButton(
            self._button_frame,
            text=self._locales.get_string('back'),
            command=_back_command
        )
        self._next_button = ctk.CTkButton(
            self._button_frame,
            text=self._locales.get_string('next'),
            command=_next_command
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._input_data_frame.grid_columnconfigure(1, weight=1)

        self._input_code_frame.grid_columnconfigure(1, weight=1)

        self._login_title.grid(row=0, column=0, sticky='ew', padx=70, pady=(5, 20))
        self._client_id_title.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self._client_id_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self._client_secret_title.grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self._client_secret_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self._redirect_uri_title.grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self._redirect_uri_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        self._input_data_frame.grid(row=1, column=0, sticky='nsew')
        self._next_button.grid(row=0, column=1, sticky='e', padx=5, pady=5)
        self._button_frame.grid(row=2, column=0, sticky='e')
        self._code_description.grid(row=0, column=0, sticky='we', padx=5, columnspan=2)
        self._link.grid(row=1, column=0, sticky='we', padx=5, columnspan=2)
        self._code_title.grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self._code_input_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

    def spotify_login(self):
        try:
            spl = SpotifyLogin.Login()
            spl.login_with_authorization_code(self._settings.get_setting('code'))

            return spl

        except SpotifyLogin.LoginDataError:
            return None

        except SpotifyLogin.AuthorizationUrlError:
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('code_error'),
                icon='cancel',
                topmost=False
            ).get()

            return False

        except SpotifyLogin.AuthorizationError:
            CTkMessagebox(
                title=self._locales.get_string('error'),
                message=self._locales.get_string('authorization_error'),
                icon='cancel',
                topmost=False
            ).get()

            return False
