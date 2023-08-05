__all__ = [
    'LcTracks'
]

from SettingsStorage import Settings


class LcTracks:
    def __init__(self):
        self._local_tracks = set()

        settings = Settings()

        self._directory = settings.get_setting('path_for_sync')
