__all__ = [
    'MultipleTracksPool'
]

import TrackDownloader
from concurrent.futures import ThreadPoolExecutor
import SettingsStorage
from urllib.parse import urlparse
import requests
import threading


class MultipleTracksPool:
    def __init__(self, directory):
        if not isinstance(directory, str):
            raise TypeError

        self._lock = threading.Lock()

        self._settings = SettingsStorage.Settings()

        self._pool = ThreadPoolExecutor(int(self._settings.get_setting('threads')))

        self._directory = directory
        self._pool_status = {
            'ok':
                {
                    'quantity': 0,
                    'list': []
                },
            'launched':
                {
                    'quantity': 0,
                    'list': set()
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

            'link_err':
                {
                    'quantity': 0,
                    'list': []
                },

            'tag_err':
                {
                    'quantity': 0,
                    'list': []
                },
            'all_tracks':
                {

                }
        }

    def add(self, link):
        if not isinstance(link, str):
            raise TypeError

        track_id = urlparse(link).path

        if '/' not in track_id:
            self._lock.acquire()
            self._pool_status['link_err']['quantity'] += 1
            self._pool_status['link_err']['list'].append(link)
            self._pool_status['all_tracks'][link] = TrackDownloader.Status.LINK_ERR
            self._lock.release()

            return link

        track_id = track_id[track_id.rfind('/') + 1:]

        try:
            track = requests.get(f'https://api.spotifydown.com/metadata/track/{track_id}', headers=TrackDownloader.Downloader.metadata_headers).json()

            if not track['success']:
                self._lock.acquire()
                self._pool_status['link_err']['quantity'] += 1
                self._pool_status['link_err']['list'].append(link)
                self._pool_status['all_tracks'][link] = TrackDownloader.Status.LINK_ERR
                self._lock.release()
                return link

        except Exception:
            self._lock.acquire()
            self._pool_status['link_err']['quantity'] += 1
            self._pool_status['link_err']['list'].append(link)
            self._pool_status['all_tracks'][link] = TrackDownloader.Status.LINK_ERR
            self._lock.release()

            return link

        query = TrackDownloader.create_download_query(track, self._directory)

        self._lock.acquire()
        self._pool_status['launched']['quantity'] += 1
        self._pool_status['launched']['list'].add(query[0])
        self._lock.release()

        self._pool.submit(self._download, link, *query)

        return query[0]

    def launched(self):
        return self._pool_status['launched']['quantity']

    def pool_status(self):
        return self._pool_status

    def _download(self, link, *args):
        match TrackDownloader.Downloader(*args).status():
            case TrackDownloader.Status.OK:
                self._lock.acquire()
                self._pool_status['ok']['quantity'] += 1
                self._pool_status['ok']['list'].append(args[0])
                self._pool_status['all_tracks'][args[0]] = TrackDownloader.Status.OK
                self._lock.release()

            case TrackDownloader.Status.GET_ERR | TrackDownloader.Status.API_ERR:
                self._lock.acquire()
                self._pool_status['get_err']['quantity'] += 1
                self._pool_status['get_err']['list'].append(
                    {
                        'name': args[0],
                        'link': link
                    }
                )
                self._pool_status['all_tracks'][args[0]] = TrackDownloader.Status.GET_ERR
                self._lock.release()

            case TrackDownloader.Status.JPG_ERR:
                self._lock.acquire()
                self._pool_status['jpg_err']['quantity'] += 1
                self._pool_status['jpg_err']['list'].append(
                    {
                        'name': args[0],
                        'link': link
                    }
                )
                self._pool_status['all_tracks'][args[0]] = TrackDownloader.Status.JPG_ERR
                self._lock.release()

            case TrackDownloader.Status.NF_ERR:
                self._lock.acquire()
                self._pool_status['nf_err']['quantity'] += 1
                self._pool_status['nf_err']['list'].append(
                    {
                        'name': args[0],
                        'link': link
                    }
                )
                self._pool_status['all_tracks'][args[0]] = TrackDownloader.Status.NF_ERR
                self._lock.release()

            case TrackDownloader.Status.TAG_ERR:
                self._lock.acquire()
                self._pool_status['tag_err']['quantity'] += 1
                self._pool_status['tag_err']['list'].append(
                    {
                        'name': args[0],
                        'link': link
                    }
                )
                self._pool_status['all_tracks'][args[0]] = TrackDownloader.Status.TAG_ERR
                self._lock.release()

        self._lock.acquire()
        self._pool_status['launched']['quantity'] -= 1
        self._pool_status['launched']['list'].remove(args[0])
        self._lock.release()
