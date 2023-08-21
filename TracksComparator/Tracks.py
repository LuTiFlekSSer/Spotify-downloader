__all__ = [
    'Comparator'
]

import SettingsStorage


class Comparator:
    def __init__(self, local_tracks, spotify_tracks, tracks_info):
        if not isinstance(local_tracks, set) or not isinstance(spotify_tracks, set) or not isinstance(tracks_info, dict):
            raise TypeError

        self._local_missing_tracks = {}

        for track in spotify_tracks - local_tracks:
            self._local_missing_tracks[track] = tracks_info[track]

        settings = SettingsStorage.Settings()
        self._server_missing_tracks = local_tracks - spotify_tracks - settings.get_all_server_ignore_tracks()

    def get_local_missing_tracks(self):
        return self._local_missing_tracks

    def get_server_missing_tracks(self):
        return self._server_missing_tracks
