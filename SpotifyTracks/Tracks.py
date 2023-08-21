__all__ = [
    'SpTracks'
]

from SpotifyTracks import Errors
from SpotifyLogin import Login
import tqdm
from SettingsStorage import Settings


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

    def start(self):
        self._total = self._client.current_user_saved_tracks(limit=1)['total']

        self._spotify_tracks.clear()
        self._tracks_info.clear()

        settings = Settings()
        local_ignore_list = settings.get_all_local_ignore_tracks()

        try:
            for offset in tqdm.trange(0, self._total, self._limit, desc='Чтение треков из spotify'):
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
                    self._spotify_tracks.add(name.translate(str.maketrans(SpTracks.dict_for_replace)))

        except Exception:
            raise Errors.TracksGetError

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
