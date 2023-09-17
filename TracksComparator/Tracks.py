__all__ = [
    'Comparator'
]

import SettingsStorage


class Comparator:
    def __init__(self, local_tracks, spotify_tracks, tracks_info):
        if not isinstance(local_tracks, set) or not isinstance(spotify_tracks, set) or not isinstance(tracks_info, dict):
            raise TypeError

        self._local_tracks = local_tracks
        self._spotify_tracks = spotify_tracks
        self._tracks_info = tracks_info

        self._local_missing_tracks = None
        self._server_missing_tracks = None

        self._refresh()

    def _refresh(self):
        self._local_missing_tracks = {}

        for track in self._spotify_tracks - self._local_tracks:
            self._local_missing_tracks[track] = self._tracks_info[track]

        settings = SettingsStorage.Settings()
        self._server_missing_tracks = self._local_tracks - self._spotify_tracks - settings.get_all_server_ignore_tracks()

    def get_local_missing_tracks(self, refresh=False):
        if refresh:
            self._refresh()

        return self._local_missing_tracks

    def get_server_missing_tracks(self, refresh=False):
        if refresh:
            self._refresh()

        return sorted(self._server_missing_tracks)
