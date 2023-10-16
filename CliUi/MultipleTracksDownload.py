import os
from progress.spinner import PixelSpinner
import win32com.client
import time
import DownloaderPool
import Utils
from urllib.parse import urlparse


class MultipleTracksDownload:
    def __init__(self):
        pass

    def _print_menu(self):
        os.system('cls')
        print(f'{Utils.cyan("Загрузка отдельных треков")}\n\n'
              f'{Utils.blue("[1]")} - Статистика по трекам\n'
              f'{Utils.blue("[2]")} - Успешно загруженные треки\n'
              f'{Utils.blue("[3]")} - Запущенные загрузки\n'
              f'{Utils.blue("[4]")} - Треки с ошибкой изменения обложки\n'
              f'{Utils.blue("[5]")} - Треки с ошибкой при загрузке\n'
              f'{Utils.blue("[6]")} - Не найденные треки\n'
              f'{Utils.blue("[7]")} - Некорректные ссылки\n\n'
              f'{Utils.purple("[c]")} - Очистка ввода\n'
              f'{Utils.purple("[b]")} - Назад')

    def multiple_tracks_download(self):
        self._print_menu()

        try:
            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку для сохранения треков', 16, "").Self.path
        except Exception:
            print(Utils.red('Загрузка отменена'))
            time.sleep(1)
            return

        print(Utils.yellow('Для загрузки треков поочередно вводи ссылку'))

        mtp = DownloaderPool.MultipleTracksPool(directory)

        while True:
            mtp_status = mtp.pool_status()
            match (link := Utils.g_input('> ')):
                case '1':
                    print(f'{Utils.green("Успешно загружено:")} {mtp_status["ok"]["quantity"]}\n'
                          f'{Utils.blue("Запущенные загрузки:")} {mtp_status["launched"]["quantity"]}\n'
                          f'{Utils.yellow("Ошибка при изменении обложки:")} {mtp_status["jpg_err"]["quantity"]}\n'
                          f'{Utils.red("Ошибка при загрузке:")} {mtp_status["get_err"]["quantity"]}\n'
                          f'{Utils.red("Не найдено:")} {mtp_status["nf_err"]["quantity"]}\n'
                          f'{Utils.red("Некорректные ссылки:")} {mtp_status["link_err"]["quantity"]}')

                case '2':
                    if len(mtp_status['ok']['list']) == 0:
                        print(Utils.yellow('Список пуст'))
                        continue

                    for i, track in enumerate(mtp_status['ok']['list']):
                        print(f'{i + 1}) {track}')

                case '3':
                    if len(mtp_status['launched']['list']) == 0:
                        print(Utils.yellow('Список пуст'))
                        continue

                    for i, track in enumerate(mtp_status['launched']['list']):
                        print(f'{i + 1}) {track}')

                case '5':
                    if len(mtp_status['get_err']['list']) == 0:
                        print(Utils.yellow('Список пуст'))
                        continue

                    for i, track in enumerate(mtp_status['get_err']['list']):
                        print(f'{i + 1}) {track}')

                case '4':
                    if len(mtp_status['jpg_err']['list']) == 0:
                        print(Utils.yellow('Список пуст'))
                        continue

                    for i, track in enumerate(mtp_status['jpg_err']['list']):
                        print(f'{i + 1}) {track}')

                case '6':
                    if len(mtp_status['nf_err']['list']) == 0:
                        print(Utils.yellow('Список пуст'))
                        continue

                    for i, track in enumerate(mtp_status['nf_err']['list']):
                        print(f'{i + 1}) {track}')

                case '7':
                    if len(mtp_status['link_err']['list']) == 0:
                        print(Utils.yellow('Список пуст'))
                        continue

                    for i, track in enumerate(mtp_status['link_err']['list']):
                        print(f'{i + 1}) {track}')

                case 'c':
                    self._print_menu()

                case 'b':
                    if mtp.launched() != 0:
                        spinner = PixelSpinner(Utils.Colors.YELLOW + 'Ожидание окончания загрузки треков ')
                        t = time.time()
                        spinner.next()

                        while True:
                            if time.time() - t >= 0.5:
                                spinner.next()
                                t = time.time()

                                if mtp.launched() == 0:
                                    break

                        spinner.finish()

                    print(Utils.green('Возврат в меню'))
                    time.sleep(1)
                    break
                case _:
                    if urlparse(link).scheme:
                        mtp.add(link)
                    else:
                        print(Utils.red('Ошибка ввода'))
