import string
import os
import win32com.client
import SettingsStorage
import re
import sys
import __main__
import enum


# todo заменить все принты
class DownloadMode(enum.Enum):
    SYNC = 0
    COMP = 1
    PLAYLIST = 2
    MULTIPLE = 3


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


def set_sync_path(window_name):
    settings = SettingsStorage.Settings()

    try:
        directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, window_name, 16, "").Self.path
        settings.change_setting('path_for_sync', directory)

        return True

    except Exception:
        return False


def compare_versions(curr_version, new_version):
    pattern = r'^\d+\.\d+\.\d+$'

    if re.fullmatch(pattern, curr_version) is None or re.fullmatch(pattern, new_version) is None:
        raise ValueError

    if curr_version.split('.') < new_version.split('.'):
        return True

    return False


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
        return
    elif isinstance(track_list, str):
        if track_list not in tracks:
            raise ValueError

        try:
            add(track_list)

        except SettingsStorage.AlreadyExistsError:
            pass

        return

    for r in track_list:
        for i in range(r[0], r[-1] + 1):
            try:
                add(tracks[i - 1])
            except SettingsStorage.AlreadyExistsError:
                pass


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
