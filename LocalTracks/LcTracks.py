__all__ = [
    'LcTracks'
]

from SettingsStorage import Settings
from os import listdir
from LocalTracks import Errors
from progress.bar import IncrementalBar


class LcTracks:
    def __init__(self, directory=None):
        if directory is not None and not isinstance(directory, str):
            raise TypeError

        settings = Settings()
        self._directory = settings.get_setting('path_for_sync')

        if directory is not None:
            self._directory = directory
        elif self._directory == '':
            raise Errors.PathError

        self._local_tracks = set()
        self._get_tracks_from_folder()

    def _get_tracks_from_folder(self):
        tracks = listdir(self._directory)

        self._local_tracks.clear()

        for track in IncrementalBar('Чтение треков с диска', max=len(tracks), suffix='%(percent)d%% [%(elapsed_td)s / %(eta_td)s]').iter(tracks):
            if track.endswith('.mp3'):
                self._local_tracks.add(track[:-4])

    def get_numbers_of_tracks(self):
        return len(self._local_tracks)

    def get_local_tracks(self):
        return self._local_tracks
