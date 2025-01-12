__all__ = [
    'SpTracks'
]

from SpotifyTracks import Errors
from SpotifyLogin import Login
from SettingsStorage import Settings
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Lock


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
        self._lock = Lock()

    def start(self):
        try:
            self._total = self._client.current_user_saved_tracks(limit=1)['total']

            self._spotify_tracks.clear()
            self._tracks_info.clear()

            settings = Settings()
            local_ignore_list = settings.get_all_local_ignore_tracks()

            pool = ThreadPoolExecutor(int(settings.get_setting('threads')))

            runs = [pool.submit(self._get_tracks, offset, local_ignore_list) for offset in
                    range(0, self._total, self._limit)]
            checked = [False for _ in runs]

            completed = 0

            for _ in runs:
                i = 0

                while True:
                    time.sleep(0.01)

                    if not checked[i] and runs[i].done():
                        checked[i] = True
                        completed += self._limit

                        try:
                            runs[i].result()
                        except Exception as ex:
                            print(ex)
                            pool.shutdown(cancel_futures=True)

                            raise Errors.TracksGetError

                        break

                    i += 1
                    if i == len(runs):
                        i = 0

                yield completed, self._total


        except Exception:
            raise Errors.TracksGetError

    def _get_tracks(self, offset, local_ignore_list):
        attempts = 0
        while True:
            try:
                tracks = self._client.current_user_saved_tracks(limit=self._limit, offset=offset)['items']

                break
            except Exception as ex:
                if attempts == 3:
                    raise ex
                else:
                    time.sleep(0.5)

            attempts += 1

        for track in tracks:
            name = track['track']['name'] + ' - '

            artists = [aut['name'] for aut in track['track']['artists']]

            name += '\u29f8'.join(artists)
            name = name.translate(str.maketrans(SpTracks.dict_for_replace))

            if name in local_ignore_list:
                continue

            self._lock.acquire()
            self._tracks_info[name] = {
                'id': track['track']['id'],
                'name': track['track']['name'],
                'artists': [aut['name'] for aut in track['track']['artists']],
                'album_name': track['track']['album']['name'],
                'release_date': track['track']['album']['release_date'][:4],
                'cover': track['track']['album']['images'][0]['url']
            }
            self._spotify_tracks.add((name, track['track']['id']))
            self._lock.release()

    def refresh_track_list(self):
        settings = Settings()
        local_ignore = settings.get_all_local_ignore_tracks()

        tracks_with_id = [(track, track_id) for track, track_id in self._spotify_tracks if track in local_ignore]
        for track in tracks_with_id:
            self._total -= 1
            self._spotify_tracks.remove(track)
            self._tracks_info.pop(track[0])

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
