__all__ = [
    'PlaylistPool'
]

import time
import TrackDownloader
from concurrent.futures import ThreadPoolExecutor, CancelledError
import SettingsStorage
import threading
import msvcrt
from progress.bar import IncrementalBar
from progress.spinner import PixelSpinner
from CliUi import Utils
import os


class PlaylistPool:
    def __init__(self, header):
        self._settings = SettingsStorage.Settings()

        self._pool = ThreadPoolExecutor(int(self._settings.get_setting('threads')))

        self._header = header
        self._pool_results = None
        self._cancelled = False
        self._stopper_on = True
        self._pool_status = {
            'ok':
                {
                    'quantity': 0,
                    'list': []
                },

            'cancelled':
                {
                    'quantity': 0,
                    'list': []
                },

            'api_err':
                {
                    'quantity': 0,
                    'list': []
                },

            'get_err':
                {
                    'quantity': 0,
                    'list': []
                },

            'jpg_err':
                {
                    'quantity': 0,
                    'list': []
                },

            'nf_err':
                {
                    'quantity': 0,
                    'list': []
                }
        }

    def start(self, track_list):
        self._pool_results = [[self._pool.submit(TrackDownloader.Downloader, *track), track[0]] for track in track_list]
        checked = [False for _ in track_list]

        stopper = threading.Thread(target=self._stop)
        stopper.start()

        bar = IncrementalBar('Загрузка треков', max=len(track_list), suffix='%(percent)d%% [%(elapsed_td)s / %(eta_td)s]')
        spinner = PixelSpinner(Utils.Colors.YELLOW + 'Отмена загрузки, ожидание запущенных загрузок ')
        bar.start()
        last_time = 0

        for _ in track_list:
            i = 0

            while True:
                time.sleep(0.01)

                if not checked[i] and (self._pool_results[i][0].done()):
                    checked[i] = True
                    break

                i += 1
                if i == len(track_list):
                    i = 0

                if self.cancelled() and time.time() - last_time >= 0.5:
                    spinner.next()
                    last_time = time.time()

            if not self._cancelled:
                bar.next()

        self._stopper_on = False
        stopper.join()

        bar.finish()
        spinner.finish()

        while msvcrt.kbhit():
            msvcrt.getch()

        for task in self._pool_results:
            try:
                match task[0].result().status():
                    case TrackDownloader.Status.OK:
                        self._pool_status['ok']['quantity'] += 1
                        self._pool_status['ok']['list'].append(task[1])

                    case TrackDownloader.Status.API_ERR:
                        self._pool_status['api_err']['quantity'] += 1
                        self._pool_status['api_err']['list'].append(task[1])

                    case TrackDownloader.Status.GET_ERR:
                        self._pool_status['get_err']['quantity'] += 1
                        self._pool_status['get_err']['list'].append(task[1])

                    case TrackDownloader.Status.JPG_ERR:
                        self._pool_status['jpg_err']['quantity'] += 1
                        self._pool_status['jpg_err']['list'].append(task[1])

                    case TrackDownloader.Status.NF_ERR:
                        self._pool_status['nf_err']['quantity'] += 1
                        self._pool_status['nf_err']['list'].append(task[1])

            except CancelledError:
                self._pool_status['cancelled']['quantity'] += 1
                self._pool_status['cancelled']['list'].append(task[1])

    def _stop(self):
        while self._stopper_on:
            if msvcrt.kbhit() and msvcrt.getch() == b'b':
                break

            time.sleep(0.1)

        else:
            return

        self._cancelled = True

        os.system('cls')
        print(self._header)

        for task in self._pool_results:
            if not task[0].running():
                task[0].cancel()

    def cancelled(self):
        return self._cancelled

    def pool_status(self):
        return self._pool_status
