__all__ = [
    'SpTracks'
]

from SpotifyTracks import Errors
from SpotifyLogin import Login
from SettingsStorage import Settings
from progress.bar import IncrementalBar
from concurrent.futures import ThreadPoolExecutor
import time
import threading


class SpTracks:
    dict_for_replace = {
        '/': '\u29f8',
        '\\': '\u29f9',
        ':': '\ua4fd',
        '"': '\u2033',
        '*': '\u204e',
        '?': '\u0294',
        '<': '\u1438',
        '>': '\u1433',
        '|': '\u2223'
    }

    def __init__(self, client):
        if not isinstance(client, Login):
            raise TypeError

        self._client = client.get_client()

        if self._client is None:
            raise Errors.ClientError

        self._limit = 50
        self._total = 0
        self._spotify_tracks = set()
        self._tracks_info = {}
        self._updater_on = True

    def start(self):
        self._total = self._client.current_user_saved_tracks(limit=1)['total']

        self._spotify_tracks.clear()
        self._tracks_info.clear()

        settings = Settings()
        local_ignore_list = settings.get_all_local_ignore_tracks()

        try:
            pool = ThreadPoolExecutor(int(settings.get_setting('threads')))

            runs = [pool.submit(self._get_tracks, offset, local_ignore_list) for offset in range(0, self._total, self._limit)]

            checked = [False for _ in runs]

            bar = IncrementalBar('Чтение треков из spotify', max=self._total / self._limit, suffix='%(percent)d%% [%(elapsed_td)s / %(eta_td)s]')
            bar.start()

            t = threading.Thread(target=self._bar_updater, args=(bar,))
            t.start()
            for _ in runs:
                i = 0

                while True:
                    time.sleep(0.01)

                    if not checked[i] and runs[i].done():
                        checked[i] = True

                        try:
                            runs[i].result()
                        except Exception:
                            pool.shutdown(cancel_futures=True)

                            self._updater_on = False
                            t.join()

                            raise Errors.TracksGetError

                        break

                    i += 1
                    if i == len(runs):
                        i = 0

                bar.next()

            self._updater_on = False
            t.join()

        except Exception:
            raise Errors.TracksGetError

    def _bar_updater(self, bar):
        while self._updater_on:
            time.sleep(0.1)
            bar.update()

    def _get_tracks(self, offset, local_ignore_list):
        for track in self._client.current_user_saved_tracks(limit=self._limit, offset=offset)['items']:
            name = track['track']['name'] + ' - '

            artists = [aut['name'] for aut in track['track']['artists']]

            name += '\u29f8'.join(artists)

            if name in local_ignore_list:
                continue

            self._tracks_info[name.translate(str.maketrans(SpTracks.dict_for_replace))] = {
                'id': track['track']['id'],
                'name': track['track']['name'],
                'artists': [aut['name'] for aut in track['track']['artists']],
                'album_name': track['track']['album']['name'],
                'release_date': track['track']['album']['release_date'][:4]
            }
            self._spotify_tracks.add((name.translate(str.maketrans(SpTracks.dict_for_replace)), track['track']['id']))

    def refresh_track_list(self):
        settings = Settings()

        for track in settings.get_all_local_ignore_tracks():
            if track in self._spotify_tracks:
                self._total -= 1
                self._spotify_tracks.remove(track)
                self._tracks_info.pop(track)

    def set_limit(self, limit):
        if not isinstance(limit, int):
            raise TypeError

        if 1 <= limit <= 50:
            self._limit = limit
        else:
            raise ValueError

    def get_number_of_tracks(self):
        return self._total

    def get_spotify_tracks(self):
        return self._spotify_tracks

    def get_tracks_info(self):
        return self._tracks_info
