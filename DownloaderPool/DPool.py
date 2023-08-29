__all__ = [
    'PlaylistPool'
]

import TrackDownloader
from concurrent.futures import ThreadPoolExecutor
import SettingsStorage
import tqdm
from pynput.keyboard import Listener, KeyCode
import msvcrt
import time
from progress.bar import IncrementalBar


class PlaylistPool:
    def __init__(self):
        self._settings = SettingsStorage.Settings()

        self._pool = ThreadPoolExecutor(int(self._settings.get_setting('threads')))

        self._pool_results = None

    def start(self, track_list):
        self._pool_results = [self._pool.submit(TrackDownloader.Downloader, *track) for track in track_list]
        checked = [False for _ in track_list]

        listener = Listener(on_release=self._stop)
        listener.start()

        bar = IncrementalBar('Загрузка треков', max=len(track_list))
        bar.start()

        for _ in track_list:
            i = 0

            while True:
                if not checked[i] and ((task := self._pool_results[i]).cancelled() or task.done()):
                    checked[i] = True
                    break

                i += 1
                if i == len(track_list):
                    i = 0

            bar.next()

        bar.finish()

        while msvcrt.kbhit():
            msvcrt.getch()

        listener.stop()

    def _stop(self, key):
        if key != KeyCode.from_char('b'):
            return

        for task in self._pool_results:
            if not task.running():
                task.cancel()

        print(f'Загрузка отменена')
