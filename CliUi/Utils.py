import DownloaderPool
import time
import os
import win32com.client
import SettingsStorage


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


def start_playlist_download(header, tracks):
    os.system('cls')
    print(header)

    print(f'\n{purple("[b]")} - Для отмены загрузки (запущенные потоки не будут остановлены)\n')

    pp = DownloaderPool.PlaylistPool(header)
    pp.start(tracks)

    os.system('cls')
    print(header)

    pp_status = pp.pool_status()

    def print_results():
        if pp.cancelled():
            print(red('Загрузка отменена'))
        else:
            print(green('Загрузка завершена'))

        print(f'\nСтатистика по трекам:\n'
              f'{green("Успешно загружено:")} {pp_status["ok"]["quantity"]}\n'
              f'{yellow("Ошибка при изменении обложки:")} {pp_status["jpg_err"]["quantity"]}\n'
              f'{red("Ошибка при загрузке:")} {pp_status["get_err"]["quantity"] + pp_status["api_err"]["quantity"]}\n'
              f'{red("Не найдено:")} {pp_status["nf_err"]["quantity"]}\n'
              f'{red("Отменено:")} {pp_status["cancelled"]["quantity"]}\n')

        print(f'\n{blue("[1]")} - Успешно загруженные треки\n'
              f'{blue("[2]")} - Треки с ошибкой изменения обложки\n'
              f'{blue("[3]")} - Треки с ошибкой при загрузке\n'
              f'{blue("[4]")} - Не найденные треки\n'
              f'{blue("[5]")} - Отмененне треки\n\n'
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

            case '3':
                if len(pp_status['get_err']['list'] + pp_status['api_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['get_err']['list'] + pp_status['api_err']['list']):
                    print(f'{i + 1}) {track}')

            case '2':
                if len(pp_status['jpg_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['jpg_err']['list']):
                    print(f'{i + 1}) {track}')

            case '4':
                if len(pp_status['nf_err']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['nf_err']['list']):
                    print(f'{i + 1}) {track}')

            case '5':
                if len(pp_status['cancelled']['list']) == 0:
                    print(yellow('Список пуст'))
                    continue

                for i, track in enumerate(pp_status['cancelled']['list']):
                    print(f'{i + 1}) {track}')

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


class Colors:
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
