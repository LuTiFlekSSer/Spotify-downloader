import string
import DownloaderPool
import time
import os
import win32com.client
import SettingsStorage
import re
import sys
import __main__


# todo заменить все принты

def map_value(curr_value, max_value):
    return curr_value / max_value


def get_executable_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    elif __file__:
        return os.path.abspath(__main__.__file__)
    else:
        return None


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def set_sync_path(print_menu):
    print(red(f'{Colors.BLINK}Не задан путь к папке для синхронизации, задать сейчас?') + yellow(' (y - да, n - нет)'))

    settings = SettingsStorage.Settings()

    while True:
        match input('> '):
            case 'y':

                try:
                    directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку с треками', 16, "").Self.path
                    settings.change_setting('path_for_sync', directory)

                    print(f'{green("Путь изменен на:")} {directory}\n')
                    time.sleep(1)

                    print_menu()

                    return True
                except Exception:
                    print(red('Проверка отменена'))
                    time.sleep(1)

                    return False
            case 'n':
                print(green('Возврат в меню'))
                time.sleep(1)
                return False
            case _:
                print(red('Ошибка ввода'))


def compare_versions(curr_version, new_version):
    pattern = r'^\d+\.\d+\.\d+$'

    if re.fullmatch(pattern, curr_version) is None or re.fullmatch(pattern, new_version) is None:
        raise ValueError

    if curr_version.split('.') < new_version.split('.'):
        return True

    return False


def start_playlist_download(header, tracks, sync=False):
    pp = DownloaderPool.PlaylistPool(header, sync)

    def start():
        os.system('cls')
        print(header)

        print(f'\n{purple("[b]")} - Для отмены загрузки (запущенные потоки не будут остановлены)\n')

        pp.start(tracks)

        os.system('cls')
        print(header)

        return pp

    pp = start()

    pp_status = pp.pool_status()

    def print_results():
        if pp.cancelled():
            print(red('Загрузка отменена'))
        else:
            print(green('Загрузка завершена'))

        print(f'\nСтатистика по трекам:\n'
              f'{green("Успешно загружено:")} {pp_status["ok"]["quantity"]}\n'
              f'{yellow("Ошибка при изменении обложки:")} {pp_status["jpg_err"]["quantity"]}\n'
              f'{yellow("Ошибка при изменении метаданных:")} {pp_status["jpg_err"]["quantity"]}\n'
              f'{red("Ошибка при загрузке:")} {pp_status["get_err"]["quantity"]}\n'
              f'{red("Не найдено:")} {pp_status["nf_err"]["quantity"]}\n'
              f'{red("Отменено:")} {pp_status["cancelled"]["quantity"]}\n')

        print(f'\n{blue("[1]")} - Успешно загруженные треки\n'
              f'{blue("[2]")} - Треки с ошибкой изменения обложки\n'
              f'{blue("[3]")} - Треки с ошибкой изменения метаданных\n'
              f'{blue("[4]")} - Треки с ошибкой при загрузке\n'
              f'{blue("[5]")} - Не найденные треки\n'
              f'{blue("[6]")} - Отмененные треки\n\n'
              f'{purple("[r]")} - Перезапустить неудачные загрузки\n'
              f'{purple("[c]")} - Очистка ввода\n'
              f'{purple("[b]")} - Назад')

    print_results()

    while True:
        match g_input('> '):
            case '1':
                if len(pp_status['ok']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['ok']['list']):
                    print(f'{i + 1}) {track}')

            case '2':
                if len(pp_status['jpg_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['jpg_err']['list']):
                    print(f'{i + 1}) {track}')

            case '3':
                if len(pp_status['tag_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['tag_err']['list']):
                    print(f'{i + 1}) {track}')

            case '4':
                if len(pp_status['get_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['get_err']['list']):
                    print(f'{i + 1}) {track}')

            case '5':
                if len(pp_status['nf_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['nf_err']['list']):
                    print(f'{i + 1}) {track}')

            case '6':
                if len(pp_status['cancelled']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['cancelled']['list']):
                    print(f'{i + 1}) {track}')

            case 'r':
                tracks = [track for track in tracks if track[0] not in pp_status['ok']['list']]

                if len(tracks) == 0:
                    print(yellow('Неудачных загрузок нет'))
                    continue

                pp.clear_tracks_with_error()
                pp = start()

                pp_status = pp.pool_status()

                os.system('cls')
                print(header)
                print_results()

            case 'c':
                os.system('cls')
                print(header)
                print_results()

            case 'b':
                print(green('Возврат в меню'))
                time.sleep(1)
                break

            case _:
                print(red('Ошибка ввода'))


def _parse_numbers(numbers: str):
    ranges = [list(map(int, number.split('-'))) for number in numbers.replace(' ', '').split(',')]

    for i, r in enumerate(ranges):
        for j, number in enumerate(r[:-1]):
            if number >= r[j + 1]:
                raise ValueError

        if i < len(ranges) - 1:
            if r[-1] >= ranges[i + 1][0]:
                raise ValueError

    return ranges


def _input_parser(tracks, tracks_input):
    if tracks_input == '':
        raise ValueError

    if tracks_input in tracks or set(tracks_input) - set(string.digits + ' ,-'):
        return tracks_input

    numbers_range = _parse_numbers(tracks_input)

    if numbers_range[0][0] <= 0 or numbers_range[-1][-1] > len(tracks):
        raise IndexError

    return numbers_range


def add_tracks_to_ignore(tracks, add, tracks_input):
    track_list = _input_parser(tracks, tracks_input)

    if track_list is None:
        return False
    elif isinstance(track_list, str):
        try:
            add(track_list)

            print(f'{Colors.GREEN}Трек {Colors.END}"{track_list}"{Colors.GREEN} добавлен в игнор лист{Colors.END}')

            return True

        except SettingsStorage.AlreadyExistsError:
            print(f'{Colors.RED}Трек {Colors.END}"{track_list}"{Colors.RED} уже был добавлен игнор лист{Colors.END}')

            return False

    for r in track_list:
        for i in range(r[0], r[-1] + 1):
            try:
                add(tracks[i - 1])
            except SettingsStorage.AlreadyExistsError:
                print(f'{Colors.RED}Трек {Colors.END}"{tracks[i - 1]}"{Colors.RED} уже был добавлен игнор лист{Colors.END}')

    print(green('Треки добавлены в игнор лист'))
    return True


def remove_tracks_from_ignore(tracks, remove, tracks_input):
    track_list = _input_parser(tracks, tracks_input)

    if track_list is None:
        return

    elif isinstance(track_list, str):
        remove(track_list)

        return

    for r in track_list:
        for i in range(r[0], r[-1] + 1):
            remove(tracks[i - 1])


class Colors:  # todo удалить цвета
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    BLINK = '\033[6m'


def purple(s):
    return Colors.PURPLE + s + Colors.END


def blue(s):
    return Colors.BLUE + s + Colors.END


def cyan(s):
    return Colors.CYAN + s + Colors.END


def green(s):
    return Colors.GREEN + s + Colors.END


def yellow(s):
    return Colors.YELLOW + s + Colors.END


def red(s):
    return Colors.RED + s + Colors.END


def bold(s):
    return Colors.BOLD + s + Colors.END


def g_input(s):
    inp = input(bold(s) + Colors.GREEN)
    print(Colors.END, end='')
    return inp
