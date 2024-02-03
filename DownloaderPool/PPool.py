__all__ = [
    'PlaylistPool'
]

import time
import TrackDownloader
from concurrent.futures import ThreadPoolExecutor, CancelledError
import SettingsStorage
import threading


class PlaylistPool:
    def __init__(self, sync=False):
        self._settings = SettingsStorage.Settings()

        self._pool = ThreadPoolExecutor(int(self._settings.get_setting('threads')))

        self._lock = threading.Lock()

        self._sync = sync
        self._pool_results = None
        self._cancelled = False
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
                },

            'tag_err':
                {
                    'quantity': 0,
                    'list': []
                },
        }

    def start(self, track_list):
        self._pool_results = [[self._pool.submit(TrackDownloader.Downloader, *track, self._sync), track[0]] for track in track_list]
        checked = [False for _ in track_list]

        downloaded_count = 0
        i = 0
        while True:
            time.sleep(0.001)

            self._lock.acquire()
            if not checked[i] and (self._pool_results[i][0].done()):
                checked[i] = True
                downloaded_count += 1

                try:
                    yield i, self._pool_results[i][0].result().status()
                except CancelledError:
                    yield i, TrackDownloader.Status.CANCELLED

            self._lock.release()

            i += 1
            if i == len(track_list):
                i = 0

            if downloaded_count == len(track_list):
                break

        for task in self._pool_results:
            try:
                match task[0].result().status():
                    case TrackDownloader.Status.OK:
                        self._pool_status['ok']['quantity'] += 1
                        self._pool_status['ok']['list'].append(task[1])

                    case TrackDownloader.Status.GET_ERR | TrackDownloader.Status.API_ERR:
                        self._pool_status['get_err']['quantity'] += 1
                        self._pool_status['get_err']['list'].append(task[1])

                    case TrackDownloader.Status.JPG_ERR:
                        self._pool_status['jpg_err']['quantity'] += 1
                        self._pool_status['jpg_err']['list'].append(task[1])

                    case TrackDownloader.Status.NF_ERR:
                        self._pool_status['nf_err']['quantity'] += 1
                        self._pool_status['nf_err']['list'].append(task[1])

                    case TrackDownloader.Status.TAG_ERR:
                        self._pool_status['tag_err']['quantity'] += 1
                        self._pool_status['tag_err']['list'].append(task[1])

            except CancelledError:
                self._pool_status['cancelled']['quantity'] += 1
                self._pool_status['cancelled']['list'].append(task[1])

    def stop(self):
        self._cancelled = True

        self._lock.acquire()
        for task in self._pool_results:
            if not task[0].running():
                task[0].cancel()
        self._lock.release()

    def clear_tracks_with_error(self):
        for error in ['get_err', 'jpg_err', 'nf_err', 'tag_err', 'cancelled']:
            self._pool_status[error]['quantity'] = 0
            self._pool_status[error]['list'].clear()

        self._cancelled = False

    def cancelled(self):
        return self._cancelled

    def pool_status(self):
        return self._pool_status
