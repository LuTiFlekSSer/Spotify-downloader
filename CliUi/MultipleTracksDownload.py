import os
from progress.spinner import PixelSpinner
import win32com.client
import time
import DownloaderPool


class MultipleTracksDownload:
    def __init__(self):
        pass

    def multiple_tracks_download(self):
        os.system('cls')
        print('Загрузка отдельных треков\n'
              '[1] - Стистика по трекам\n'
              '[2] - Успешно загруженные треки\n'
              '[3] - Запущенные загрузки\n'
              '[4] - Треки с ошибкой при загрузке\n'
              '[5] - Треки с ошибкой изменения обложки\n'
              '[6] - Не найденные треки\n'
              '[7] - Некорректные ссылки\n\n'
              '[b] - назад')

        try:
            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку для сохранения треков', 16, "").Self.path
        except Exception:
            print('Загрузка отменена')
            time.sleep(1)
            return

        print('Для загрузки треков поочередно вводи ссылку')

        mtp = DownloaderPool.MultipleTracksPool(directory)

        while True:
            mtp_status = mtp.pool_status()
            match (link := input('> ')):
                case '1':
                    print(f'Успешно загружено: {mtp_status["ok"]["quantity"]}\n'
                          f'Запущенные загрузки: {mtp_status["launched"]["quantity"]}\n'
                          f'Ошибка при загрузке: {mtp_status["get_err"]["quantity"]}\n'
                          f'Ошибка при изменении обложки: {mtp_status["jpg_err"]["quantity"]}\n'
                          f'Не найдено: {mtp_status["nf_err"]["quantity"]}\n'
                          f'Некорректные ссылки: {mtp_status["link_err"]["quantity"]}')

                case '2':
                    if len(mtp_status['ok']['list']) == 0:
                        print('Список пуст')
                        continue

                    for i, track in enumerate(mtp_status['ok']['list']):
                        print(f'{i + 1}) {track}')

                case '3':
                    if len(mtp_status['launched']['list']) == 0:
                        print('Список пуст')
                        continue

                    for i, track in enumerate(mtp_status['launched']['list']):
                        print(f'{i + 1}) {track}')

                case '4':
                    if len(mtp_status['get_err']['list']) == 0:
                        print('Список пуст')
                        continue

                    for i, track in enumerate(mtp_status['get_err']['list']):
                        print(f'{i + 1}) {track}')

                case '5':
                    if len(mtp_status['jpg_err']['list']) == 0:
                        print('Список пуст')
                        continue

                    for i, track in enumerate(mtp_status['jpg_err']['list']):
                        print(f'{i + 1}) {track}')

                case '6':
                    if len(mtp_status['nf_err']['list']) == 0:
                        print('Список пуст')
                        continue

                    for i, track in enumerate(mtp_status['nf_err']['list']):
                        print(f'{i + 1}) {track}')

                case '7':
                    if len(mtp_status['link_err']['list']) == 0:
                        print('Список пуст')
                        continue

                    for i, track in enumerate(mtp_status['link_err']['list']):
                        print(f'{i + 1}) {track}')

                case 'b':
                    spinner = PixelSpinner('Ожидание окончания загрузки треков ')
                    t = time.time()
                    spinner.next()

                    while True:
                        if time.time() - t >= 0.5:
                            spinner.next()
                            t = time.time()

                            if mtp.launched() == 0:
                                break

                    spinner.finish()
                    print('Возврат в меню')
                    time.sleep(1)
                    break
                case _:
                    mtp.add(link)
