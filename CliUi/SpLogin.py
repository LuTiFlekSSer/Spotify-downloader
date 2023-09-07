import SettingsStorage
import SpotifyLogin
import time


class SpLogin:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

    def spotify_login(self):
        try:
            spl = SpotifyLogin.Login()
            spl.login_with_authorization_code(self._settings.get_setting('code'))

        except SpotifyLogin.LoginDataError:
            print('Не заданы параметры для входа в аккаунт, задать сейчас? (y - да, n - нет)')

            while True:
                match input('> '):
                    case 'y':
                        while True:
                            s = input('Введи CLIENT ID: ')

                            if s == '':
                                print('Значение не может быть пустым')
                                continue

                            self._settings.change_setting('client_id', s)
                            break

                        while True:
                            s = input('Введи CLIENT SECRET: ')

                            if s == '':
                                print('Значение не может быть пустым')
                                continue

                            self._settings.change_setting('client_secret', s)
                            break

                        while True:
                            s = input('Введи REDIRECT URI: ')

                            if s == '':
                                print('Значение не может быть пустым')
                                continue

                            self._settings.change_setting('redirect_uri', s)
                            break

                        print('Параметры изменены\n')
                        break
                    case 'n':
                        print('Вход отменен')
                        time.sleep(1)
                        return
                    case _:
                        print('Ошибка ввода')

            spl = SpotifyLogin.Login()
            a_url = spl.get_authorization_url()

            code = input(f'Чтобы выполнить вход, необходимо перейти по ссылке и вставить полученный url, после перенаправления\n'
                         f'{a_url}\n> ')

            try:
                spl.login_with_authorization_code(code)
                self._settings.change_setting('code', code)
                print()
            except SpotifyLogin.AuthorizationUrlError:
                print('Задана некорректная ссылка с кодом')
                time.sleep(1)
                return

            except SpotifyLogin.AuthorizationError:
                print('Ошибка при входе в аккаунт')
                time.sleep(1)
                return

        except SpotifyLogin.AuthorizationUrlError:
            print('Задана некорректная ссылка с кодом')
            time.sleep(1)
            return

        except SpotifyLogin.AuthorizationError:
            print('Ошибка при входе в аккаунт')
            time.sleep(1)
            return

        return spl
