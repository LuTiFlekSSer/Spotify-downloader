import SettingsStorage
import SpotifyLogin
import time
import Utils


class SpLogin:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

    def spotify_login(self):
        try:
            spl = SpotifyLogin.Login()
            spl.login_with_authorization_code(self._settings.get_setting('code'))

        except SpotifyLogin.LoginDataError:
            print(Utils.red(f'{Utils.Colors.BLINK}Не заданы параметры для входа в аккаунт, задать сейчас?') + Utils.yellow('y - да, n - нет)'))

            while True:
                match Utils.g_input('> '):
                    case 'y':
                        while True:
                            s = Utils.g_input('Введи CLIENT ID: ')

                            if s == '':
                                print(Utils.red('Значение не может быть пустым'))
                                continue

                            self._settings.change_setting('client_id', s)
                            break

                        while True:
                            s = Utils.g_input('Введи CLIENT SECRET: ')

                            if s == '':
                                print(Utils.red('Значение не может быть пустым'))
                                continue

                            self._settings.change_setting('client_secret', s)
                            break

                        while True:
                            s = Utils.g_input('Введи REDIRECT URI: ')

                            if s == '':
                                print(Utils.red('Значение не может быть пустым'))
                                continue

                            self._settings.change_setting('redirect_uri', s)
                            break

                        print(Utils.green('Параметры изменены\n'))
                        break
                    case 'n':
                        print(Utils.green('Вход отменен'))
                        time.sleep(1)
                        return
                    case _:
                        print(Utils.red('Ошибка ввода'))

            spl = SpotifyLogin.Login()
            a_url = spl.get_authorization_url()

            code = input(f'{Utils.yellow("Чтобы выполнить вход, необходимо перейти по ссылке и вставить полученный url, после перенаправления")}\n'
                         f'{a_url}\n> ')

            try:
                spl.login_with_authorization_code(code)
                self._settings.change_setting('code', code)
                print()
            except SpotifyLogin.AuthorizationUrlError:
                print(Utils.red('Задана некорректная ссылка с кодом'))
                time.sleep(1)
                return

            except SpotifyLogin.AuthorizationError:
                print(Utils.red('Ошибка при входе в аккаунт'))
                time.sleep(1)
                return

        except SpotifyLogin.AuthorizationUrlError:
            print(Utils.red('Задана некорректная ссылка с кодом'))
            time.sleep(1)
            return

        except SpotifyLogin.AuthorizationError:
            print(Utils.red('Ошибка при входе в аккаунт'))
            time.sleep(1)
            return

        return spl
