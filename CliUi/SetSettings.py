import SettingsStorage
import os
import time
import win32com.client


def _print_settings():
    os.system('cls')
    print('Настройки\n\n'
          '[1] - Поменять кол-во потоков для загрузки треков\n'
          '[2] - Поменять путь для синхронизации треков\n'
          '[3] - Автоматически проверять отсутствующие треки на сервере при синхронизации\n'
          '[4] - Очистить данные для входа в аккаунт\n'
          '[5] - Управление локальным игнор листом\n'
          '[6] - Управление серверным игнор листом\n\n'
          '[b] - Назад\n', end='')


class SetSettings:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

    def _settings_set_threads(self):
        os.system('cls')
        print(f'Смена кол-ва потоков для загрузки треков\n\n'
              f'Текущее кол-во: {self._settings.get_setting("threads")}\n\n'
              f'[b] - назад')

        while True:
            threads = input('Введи кол-во потоков\n> ')

            if threads == 'b':
                print('Отменено')
                time.sleep(1)
                break

            if not threads.isnumeric() or threads == '0':
                print('Ошибка ввода')
                continue

            self._settings.change_setting('threads', threads)
            print(f'Кол-во потоков изменено на {threads}')
            time.sleep(1)
            break

    def _settings_set_path(self):
        os.system('cls')
        print(f'Смена папки, в которой производится синхронизация треков\n\n'
              f'Текущее расположение: {"Не задано" if (directory := self._settings.get_setting("path_for_sync")) == "" else directory}')

        print('[1] - Поменять расположение\n\n'
              '[b] - Назад')

        while True:
            match input('> '):
                case '1':
                    try:
                        directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                        self._settings.change_setting('path_for_sync', directory)

                        print(f'Путь изменен на: {directory}')
                        time.sleep(1)

                    except Exception:
                        print('Отменено')
                        time.sleep(1)

                    break

                case 'b':
                    print('Отменено')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')

    def _settings_set_auto_compare(self):
        os.system('cls')
        print(f'Автоматическое обнаружение отсуствующих треков на сервере\n\n'
              f'Текущее значение: {"Включено" if self._settings.get_setting("auto_comp") == "True" else "Выключено"}')

        print(f'[1] - {"Выключить" if self._settings.get_setting("auto_comp") == "True" else "Включить"}\n\n'
              f'[b] - Назад')

        while True:
            match input('> '):
                case '1':
                    if self._settings.get_setting("auto_comp") == "True":
                        self._settings.change_setting('auto_comp', 'False')
                        print('Выключено')
                    else:
                        self._settings.change_setting('auto_comp', 'True')
                        print('Включено')

                    time.sleep(1)
                    break

                case 'b':
                    print('Отменено')
                    time.sleep(1)
                    break

                case _:
                    print('Ошибка ввода')

    def _settings_clear_login_data(self):
        os.system('cls')
        print('Очистка данных для входа в аккаунт\n\n'
              '[1] - Очистить\n\n'
              '[b] - Назад')

        while True:
            match input('> '):
                case '1':
                    self._settings.change_setting('client_id', '')
                    self._settings.change_setting('client_sedret', '')
                    self._settings.change_setting('redirect_uri', '')
                    self._settings.change_setting('code', '')

                    try:
                        os.remove('.cache')
                    except FileNotFoundError:
                        pass

                    print('Очищено')
                    time.sleep(1)
                    break
                case 'b':
                    print('Отменено')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')

    def _settings_local_ignore_list(self):
        os.system('cls')
        print('Управление локальным игнор листом\n'
              'Эти треки будут игнорироваться при получении треков из спотифай\n')

        print('[1] - Вывести текущий список треков\n'
              '[2] - Добавить трек в игнор лист\n'
              '[3] - Удалить трек из игнор листа\n\n'
              '[b] - Назад')

        while True:
            match input('> '):
                case '1':
                    for i, name in enumerate(il := self._settings.get_all_local_ignore_tracks()):
                        print(f'{i + 1}) {name}')

                    if len(il) == 0:
                        print('Список пуст')

                case '2':
                    name = input('Введи название трека (в виде: название - автор)\n> ')

                    try:
                        self._settings.add_track_to_local_ignore(name)

                        print(f'Трек "{name}" добавлен в игнор лист')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек "{name}" уже добавлен игнор лист')

                case '3':
                    name = input('Введи название трека\n> ')

                    try:
                        self._settings.delete_track_from_local_ignore(name)
                        print(f'Трек "{name}" удален из игнор листа')

                    except SettingsStorage.NotFoundError:
                        print(f'Трек "{name}" не найден в игнор листе')

                case 'b':
                    print('Возврат в настройки')
                    time.sleep(1)
                    break

                case _:
                    print('Ошибка ввода')

    def _settings_server_ignore_list(self):
        os.system('cls')
        print('Управление серверным игнор листом\n'
              'Эти треки будут игнорироваться при поиске треков, которых нет в спотифай\n')

        print('[1] - Вывести текущий список треков\n'
              '[2] - Добавить трек в игнор лист\n'
              '[3] - Удалить трек из игнор листа\n\n'
              '[b] - Назад')

        while True:
            match input('> '):
                case '1':
                    for i, name in enumerate(il := self._settings.get_all_server_ignore_tracks()):
                        print(f'{i + 1}) {name}')

                    if len(il) == 0:
                        print('Список пуст')

                case '2':
                    name = input('Введи название трека (в виде: название - автор)\n> ')

                    try:
                        self._settings.add_track_to_server_ignore(name)

                        print(f'Трек "{name}" добавлен в игнор лист')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек "{name}" уже добавлен игнор лист')

                case '3':
                    name = input('Введи название трека\n> ')

                    try:
                        self._settings.delete_track_from_server_ignore(name)
                        print(f'Трек "{name}" удален из игнор листа')

                    except SettingsStorage.NotFoundError:
                        print(f'Трек "{name}" не найден в игнор листе')

                case 'b':
                    print('Возврат в настройки')
                    time.sleep(1)
                    break

                case _:
                    print('Ошибка ввода')

    def set_settings(self):
        _print_settings()

        while True:
            match input('> '):
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
                case 'b':
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')
