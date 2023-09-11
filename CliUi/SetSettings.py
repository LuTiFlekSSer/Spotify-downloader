import SettingsStorage
import os
import time
import win32com.client
import Utils


def _print_settings():
    os.system('cls')
    print(f'{Utils.cyan("Настройки")}\n\n'
          f'{Utils.blue("[1]")} - Поменять кол-во потоков для загрузки треков\n'
          f'{Utils.blue("[2]")} - Поменять путь для синхронизации треков\n'
          f'{Utils.blue("[3]")} - Автоматически проверять отсутствующие треки на сервере при синхронизации\n'
          f'{Utils.blue("[4]")} - Очистить данные для входа в аккаунт\n'
          f'{Utils.blue("[5]")} - Управление локальным игнор листом\n'
          f'{Utils.blue("[6]")} - Управление серверным игнор листом\n\n'
          f'{Utils.purple("[c]")} - Очистка ввода\n'
          f'{Utils.purple("[b]")} - Назад\n', end='')


class SetSettings:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

    def _settings_set_threads(self):
        def print_menu():
            os.system('cls')
            print(f'{Utils.cyan("Смена кол-ва потоков для загрузки треков")}\n\n'
                  f'{Utils.green("Текущее кол-во:")} {self._settings.get_setting("threads")}\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - назад')

        print_menu()

        while True:
            print(Utils.yellow('Введи кол-во потоков'))
            threads = Utils.g_input('> ')

            if threads == 'b':
                print(Utils.green('Возврат в настройки'))
                time.sleep(1)
                break

            if threads == 'c':
                print_menu()
                continue

            if not threads.isnumeric() or threads == '0':
                print(Utils.red('Ошибка ввода'))
                continue

            self._settings.change_setting('threads', threads)
            print(Utils.green(f'Кол-во потоков изменено на {threads}'))
            time.sleep(1)
            break

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
            print(f'{Utils.cyan("Автоматическое обнаружение отсуствующих треков на сервере")}\n\n'
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
                    self._settings.change_setting('client_sedret', '')
                    self._settings.change_setting('redirect_uri', '')
                    self._settings.change_setting('code', '')

                    try:
                        os.remove('.cache')
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
                  f'{Utils.green("Эти треки будут игнорироваться при получении треков из спотифай")}\n')

            print(f'{Utils.blue("[1]")} - Вывести текущий список треков\n'
                  f'{Utils.blue("[2]")} - Добавить трек в игнор лист\n'
                  f'{Utils.blue("[3]")} - Удалить трек из игнор листа\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    for i, name in enumerate(il := self._settings.get_all_local_ignore_tracks()):
                        print(f'{i + 1}) "{name}"')

                    if len(il) == 0:
                        print(Utils.yellow('Список пуст'))

                case '2':
                    print(Utils.yellow('Введи название трека (в виде: название - автор)'))
                    name = Utils.g_input('> ')

                    try:
                        self._settings.add_track_to_local_ignore(name)

                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} добавлен в игнор лист{Utils.Colors.END}')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} уже был добавлен игнор лист{Utils.Colors.END}')

                case '3':
                    print(Utils.yellow('Введи название трека'))
                    name = Utils.g_input('> ')

                    try:
                        self._settings.delete_track_from_local_ignore(name)
                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} удален из игнор листа{Utils.Colors.END}')

                    except SettingsStorage.NotFoundError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} не найден в игнор листе{Utils.Colors.END}')

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
                  f'{Utils.green("Эти треки будут игнорироваться при поиске треков, которых нет в спотифай")}\n')

            print(f'{Utils.blue("[1]")} - Вывести текущий список треков\n'
                  f'{Utils.blue("[2]")} - Добавить трек в игнор лист\n'
                  f'{Utils.blue("[3]")} - Удалить трек из игнор листа\n\n'
                  f'{Utils.purple("[c]")} - Очистка ввода\n'
                  f'{Utils.purple("[b]")} - Назад')

        print_menu()

        while True:
            match Utils.g_input('> '):
                case '1':
                    for i, name in enumerate(il := self._settings.get_all_server_ignore_tracks()):
                        print(f'{i + 1}) "{name}"')

                    if len(il) == 0:
                        print(Utils.yellow('Список пуст'))

                case '2':
                    print(Utils.yellow('Введи название трека (в виде: название - автор)'))
                    name = Utils.g_input('> ')

                    try:
                        self._settings.add_track_to_server_ignore(name)

                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} добавлен в игнор лист{Utils.Colors.END}')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} уже был добавлен игнор лист{Utils.Colors.END}')

                case '3':
                    print(Utils.yellow('Введи название трека'))
                    name = Utils.g_input('> ')

                    try:
                        self._settings.delete_track_from_server_ignore(name)
                        print(f'{Utils.Colors.GREEN}Трек {Utils.Colors.END}"{name}"{Utils.Colors.GREEN} удален из игнор листа{Utils.Colors.END}')

                    except SettingsStorage.NotFoundError:
                        print(f'{Utils.Colors.RED}Трек {Utils.Colors.END}"{name}"{Utils.Colors.RED} не найден в игнор листе{Utils.Colors.END}')

                case 'c':
                    print_menu()

                case 'b':
                    print(Utils.green('Возврат в настройки'))
                    time.sleep(1)
                    break

                case _:
                    print(Utils.red('Ошибка ввода'))

    def set_settings(self):
        _print_settings()

        while True:
            match Utils.g_input('> '):
                case '1':
                    self._settings_set_threads()
                    _print_settings()
                case '2':
                    self._settings_set_path()
                    _print_settings()
                case '3':
                    self._settings_set_auto_compare()
                    _print_settings()
                case '4':
                    self._settings_clear_login_data()
                    _print_settings()
                case '5':
                    self._settings_local_ignore_list()
                    _print_settings()
                case '6':
                    self._settings_server_ignore_list()
                    _print_settings()
                case 'c':
                    _print_settings()
                case 'b':
                    print(Utils.green('Возврат в меню'))
                    time.sleep(1)
                    break
                case _:
                    print(Utils.red('Ошибка ввода'))
