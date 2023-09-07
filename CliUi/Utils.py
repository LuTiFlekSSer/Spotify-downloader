import DownloaderPool
import time
import enum


def start_playlist_download(tracks):
    print('\n[b] - Для отмены загрузки (запущенные потоки не будут остановлены)\n')

    pp = DownloaderPool.PlaylistPool()
    pp.start(tracks)

    if pp.cancelled():
        print('Загрузка отменена')
    else:
        print('Загрузка завершена')

    pp_status = pp.pool_status()

    print(f'\nСтатистика по трекам:\n'
          f'Успешно загружено: {pp_status["ok"]["quantity"]}\n'
          f'Ошибка при загрузке: {pp_status["get_err"]["quantity"] + pp_status["api_err"]["quantity"]}\n'
          f'Ошибка при изменении обложки: {pp_status["jpg_err"]["quantity"]}\n'
          f'Не найдено: {pp_status["nf_err"]["quantity"]}\n'
          f'Отменено: {pp_status["cancelled"]["quantity"]}\n')

    print('\n[1] - Успешно загруженные треки\n'
          '[2] - Треки с ошибкой при загрузке\n'
          '[3] - Треки с ошибкой изменения обложки\n'
          '[4] - Не найденные треки\n'
          '[5] - Отмененне треки\n\n'
          '[b] - Назад')

    while True:
        match input('> '):
            case '1':
                if len(pp_status['ok']['list']) == 0:
                    print('Список пуст')
                    continue

                for i, track in enumerate(pp_status['ok']['list']):
                    print(f'{i + 1}) {track}')

            case '2':
                if len(pp_status['get_err']['list'] + pp_status['api_err']['list']) == 0:
                    print('Список пуст')
                    continue

                for i, track in enumerate(pp_status['get_err']['list'] + pp_status['api_err']['list']):
                    print(f'{i + 1}) {track}')

            case '3':
                if len(pp_status['jpg_err']['list']) == 0:
                    print('Список пуст')
                    continue

                for i, track in enumerate(pp_status['jpg_err']['list']):
                    print(f'{i + 1}) {track}')

            case '4':
                if len(pp_status['nf_err']['list']) == 0:
                    print('Список пуст')
                    continue

                for i, track in enumerate(pp_status['nf_err']['list']):
                    print(f'{i + 1}) {track}')

            case '5':
                if len(pp_status['cancelled']['list']) == 0:
                    print('Список пуст')
                    continue

                for i, track in enumerate(pp_status['cancelled']['list']):
                    print(f'{i + 1}) {track}')

            case 'b':
                print('Возврат в меню')
                time.sleep(1)
                break

            case _:
                print('Ошибка ввода')


class Colors(enum.Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
