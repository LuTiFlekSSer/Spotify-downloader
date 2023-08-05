__all__ = [
    'SpTracks'
]

from SpotifyTracks import Errors
from SpotifyLogin import Login


class SpTracks:
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
