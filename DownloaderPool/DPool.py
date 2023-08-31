__all__ = [
    'PlaylistPool'
]

import time

import TrackDownloader
from concurrent.futures import ThreadPoolExecutor
import SettingsStorage
from pynput.keyboard import Listener, KeyCode
import msvcrt
from progress.bar import IncrementalBar
from progress.spinner import PixelSpinner


class PlaylistPool:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

        self._pool = ThreadPoolExecutor(int(self._settings.get_setting('threads')))

        self._pool_results = None

        self._cancelled = False

    def start(self, track_list):
        self._pool_results = [self._pool.submit(TrackDownloader.Downloader, *track) for track in track_list]
        checked = [False for _ in track_list]

        listener = Listener(on_release=self._stop)
        listener.start()

        bar = IncrementalBar('Загрузка треков', max=len(track_list), suffix='%(percent)d%% [%(elapsed_td)s / %(eta_td)s]')
        spinner = PixelSpinner('Отмена загрузки ')
        bar.start()
        last_time = 0

        for _ in track_list:
            i = 0

            while True:
                if not checked[i] and (self._pool_results[i].done()):
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

        bar.finish()
        spinner.finish()

        while msvcrt.kbhit():
            msvcrt.getch()

        listener.stop()

    def _stop(self, key):
        if key != KeyCode.from_char('b'):
            return

        self._cancelled = True
        print(f'\r{" " * 80}\r', end='')

        for task in self._pool_results:
            if not task.running():
                task.cancel()

    def cancelled(self):
        return self._cancelled
