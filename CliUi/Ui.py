__all__ = [
    'Cli'
]

import os
import LocalTracks
import SettingsStorage
import SpotifyLogin
import SpotifyTracks
import TrackDownloader
import TracksComparator
import win32com.client
import time
from urllib.parse import urlparse
import requests
import DownloaderPool


def _print_greeting():
    os.system('cls')
    print('-----------------------------------------')
    print('| ADSKAYA KOCHALKA v14.88 WELCOMES YOU! |')
    print('-----------------------------------------')
    print('What do you want to do?\n\n'
          '[1] - Синхронизировать треки с аккаунтом\n'
          '[2] - Проверить отсутсвующие треки на сервере\n'
          '[3] - Скачать треки из плейлиста по ссылке\n'
          '[4] - Скачать отдельные треки по ссылке\n'
          '[5] - Настройки\n\n'
          '[x] - Выход\n', end='')


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


def _create_download_query(track, directory):
    separator = '\u29f8'

    track_info = {
        'id': track['id'],
        'name': track['title'],
        'artists': [aut.strip() for aut in track['artists'].split(',')],
        'album_name': track['album'],
        'release_date': track['releaseDate'][:4]
    }

    return f"{track_info['name']} - {separator.join(track_info['artists'])}".translate(str.maketrans(SpotifyTracks.SpTracks.dict_for_replace)), directory, track_info


class Cli:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

        self._main_page()

    def _main_page(self):
        _print_greeting()
        while True:
            match input('> '):
                case '1':
                    self._tracks_syncing()
                    _print_greeting()
                case '2':
                    self._tracks_compare()
                    _print_greeting()
                case '3':
                    self._playlist_download()
                    _print_greeting()
                case '4':
                    self._multiple_tracks_download()
                    _print_greeting()
                case '5':
                    self._set_settings()
                    _print_greeting()
                case 'x':
                    print('ББ')
                    break
                case _:
                    print('Ошибка ввода')

    def _tracks_compare(self):
        os.system('cls')
        print('Проверка отсутствующих треков на сервере\n')

        spl = self._spotify_login()

        if spl is None:
            return

        spt = SpotifyTracks.SpTracks(spl)
        spt.start()
        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        comp = TracksComparator.Comparator(set(), spotify_tracks, tracks_info)

        server_missing_tracks = comp.get_server_missing_tracks()

        if len(server_missing_tracks) == 0:
            print('\nТреки на сервере синхронизированы\n')
        else:
            print('\nСписок отсутствующих треков на сервере:\n')
            for i, track in enumerate(server_missing_tracks):
                print(f'{i + 1}) {track}')
        print()
        print('[1] - Добавить треки в серверный игнор лист\n\n'
              '[b] - назад')

        while True:
            match input('> '):
                case '1':
                    name = input('Введи название трека\n> ')
                    try:
                        self._settings.add_track_to_server_ignore(name)
                        print(f'Трек {name} добавлен в игнор лист')
                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек {name} уже добавлен в игнор лист')
                case 'b':
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')

    def _spotify_login(self):
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

    def _tracks_syncing(self):
        os.system('cls')
        print('Синхронизация треков с аккаунтом\n')

        if (path := self._settings.get_setting('path_for_sync')) == '' or not os.path.exists(path):
            print('Не задан путь к папке для синхронизации, задать сейчас? (y - да, n - нет)')

            while True:
                match input('> '):
                    case 'y':

                        try:
                            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                            self._settings.change_setting('path_for_sync', directory)

                            print(f'Путь изменен на: {directory}\n')

                            break
                        except Exception:
                            print('Синхронизация отменена')
                            time.sleep(1)

                            return
                    case 'n':
                        print('Синхронизация отменена')
                        time.sleep(1)
                        return
                    case _:
                        print('Ошибка ввода')

        spl = self._spotify_login()

        if spl is None:
            return

        spt = SpotifyTracks.SpTracks(spl)
        try:
            spt.start()
        except SpotifyTracks.TracksGetError:
            print('Ошибка при получении треков из spotify')
            time.sleep(1)
            return

        spotify_tracks = spt.get_spotify_tracks()
        tracks_info = spt.get_tracks_info()

        lct = LocalTracks.LcTracks()
        local_tracks = lct.get_local_tracks()

        comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)

        if self._settings.get_setting('auto_comp') == 'True':
            server_missing_tracks = comp.get_server_missing_tracks()

            if len(server_missing_tracks) == 0:
                print('\nТреки на сервере синхронизированы\n')
            else:
                print('\nСписок отсутствующих треков на сервере:\n')
                for i, track in enumerate(server_missing_tracks):
                    print(f'{i + 1}) {track}')
                print()

                print('[1] - Продолжить синхронизацию треков\n'
                      '[2] - Добавить треки в серверный игнор лист\n\n'
                      '[b] - Назад')

                while True:
                    match input('> '):
                        case '1':
                            break

                        case '2':
                            name = input('Введи название трека\n> ')

                            try:
                                self._settings.add_track_to_server_ignore(name)
                                print(f'Трек {name} добавлен в игнор лист')

                            except SettingsStorage.AlreadyExistsError:
                                print(f'Трек {name} уже добавлен в игнор лист')

                        case 'b':
                            print('Синхронизация прекращена')
                            time.sleep(1)
                            return

                        case _:
                            print('Ошибка ввода')

        local_missing_tracks = comp.get_local_missing_tracks()

        print()
        if len(local_missing_tracks) == 0:
            print('Локальные треки синхронизированы')
            time.sleep(1)
            return

        print('Список отсутствующих локальных треков:\n')
        for i, track in enumerate(local_missing_tracks):
            print(f'{i + 1}) {track}')

        print('\n[1] - Скачать отсутствующие треки\n'
              '[2] - Добавить треки в локальный игнор лист (новые треки будут сразу проигнорированы при загрузке)\n\n'
              '[b] - Назад')

        new_tracks = False
        while True:
            match input('> '):
                case '1':
                    break

                case '2':
                    name = input('Введи название трека\n> ')

                    try:
                        self._settings.add_track_to_local_ignore(name)
                        print(f'Трек {name} добавлен в игнор лист')
                        new_tracks = True

                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек {name} уже добавлен в игнор лист')

                case 'b':
                    print('Загрузка отменена')
                    time.sleep(1)
                    return
                case _:

                    print('Ошибка ввода')
        if new_tracks:
            spt.refresh_track_list()

            comp = TracksComparator.Comparator(local_tracks, spotify_tracks, tracks_info)
            local_missing_tracks = comp.get_local_missing_tracks()

        dp = DownloaderPool.PlaylistPool()
        dp.start([(track, self._settings.get_setting('path_for_sync'), local_missing_tracks[track]) for track in local_missing_tracks])

        if dp.cancelled():
            print('Загрузка отменена\n\n'
                  '[b] - назад')
        else:
            print('Загрузка завершена\n\n'
                  '[b] - назад')

        while True:
            match input('> '):
                case 'b':
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')

    def _playlist_download(self):
        os.system('cls')
        print('Загрузка треков из плейлиста\n')

        link = input('Введи ссылку на плейлист\n> ')

        playlist_id = urlparse(link).path

        if '/' not in playlist_id:
            print('Некорректная ссылка')
            time.sleep(1)
            return

        playlist_id = playlist_id[playlist_id.rfind('/') + 1:]

        try:
            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку для сохранения треков', 16, "").Self.path
        except Exception:
            print('Загрузка отменена')
            time.sleep(1)
            return

        playlist = []
        offset = 0

        try:
            while True:
                playlist_info = requests.get(f'https://api.spotifydown.com/trackList/playlist/{playlist_id}?offset={offset}', headers=TrackDownloader.Downloader.headers).json()

                if not playlist_info['success']:
                    print('Ошибка при загрузке информации о плейлисте')
                    time.sleep(1)
                    return

                playlist += playlist_info['trackList']

                if playlist_info['nextOffset'] is None:
                    break

                offset = playlist_info['nextOffset']

        except Exception:
            print('Ошибка при работе с сcылкой')
            time.sleep(1)
            return

        dp = DownloaderPool.PlaylistPool()
        dp.start([_create_download_query(track, directory) for track in playlist])

        print('Загрузка завершена\n\n'
              '[b] - назад')

        while True:
            match input('> '):
                case 'b':
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    print('Ошибка ввода')

    def _multiple_tracks_download(self):
        os.system('cls')
        print('Загрузка отдельных треков\n\n'
              '[b] - назад')

        try:
            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку для сохранения треков', 16, "").Self.path
        except Exception:
            print('Загрузка отменена')
            time.sleep(1)
            return
        print('Для загрузки треков поочередно вводи ссылку')

        while True:
            match (link := input('> ')):
                case 'b':
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    track_id = urlparse(link).path

                    if '/' not in track_id:
                        print('Некорректная ссылка')
                        continue

                    track_id = track_id[track_id.rfind('/') + 1:]

                    try:
                        track = requests.get(f'https://api.spotifydown.com/metadata/track/{track_id}', headers=TrackDownloader.Downloader.headers).json()

                        if not track['success']:
                            print('Ошибка при загрузке информации о треке')
                            continue

                    except Exception:
                        print('Ошибка при работе с сcылкой')
                        continue

                    TrackDownloader.Downloader(*_create_download_query(track, directory))
                    print('Загружено')

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

                        print(f'Трек {name} добавлен в игнор лист')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек {name} уже добавлен игнор лист')

                case '3':
                    name = input('Введи название трека\n> ')

                    try:
                        self._settings.delete_track_from_local_ignore(name)
                        print(f'Трек {name} удален из игнор листа')

                    except SettingsStorage.NotFoundError:
                        print(f'Трек {name} не найден в игнор листе')

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

                        print(f'Трек {name} добавлен в игнор лист')

                    except SettingsStorage.AlreadyExistsError:
                        print(f'Трек {name} уже добавлен игнор лист')

                case '3':
                    name = input('Введи название трека\n> ')

                    try:
                        self._settings.delete_track_from_server_ignore(name)
                        print(f'Трек {name} удален из игнор листа')

                    except SettingsStorage.NotFoundError:
                        print(f'Трек {name} не найден в игнор листе')

                case 'b':
                    print('Возврат в настройки')
                    time.sleep(1)
                    break

                case _:
                    print('Ошибка ввода')

    def _set_settings(self):
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
