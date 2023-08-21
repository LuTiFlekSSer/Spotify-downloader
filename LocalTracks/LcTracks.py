__all__ = [
    'LcTracks'
]

from SettingsStorage import Settings
from os import listdir
import tqdm
from LocalTracks import Errors


class LcTracks:
    def __init__(self, directory=None):
        if directory is not None and not isinstance(directory, str):
            raise TypeError

        settings = Settings()
        self._directory = settings.get_setting('path_for_sync')

        if self._directory == '':
            if directory is None:
                raise Errors.PathError

            self._directory = directory

        self._local_tracks = set()
        self._get_tracks_from_folder()

    def _get_tracks_from_folder(self):
        tracks = listdir(self._directory)

        self._local_tracks.clear()

        for track in tqdm.tqdm(tracks, desc='Чтение треков с диска'):
            if track.endswith('.mp3'):
                self._local_tracks.add(track[:-4])

    def get_numbers_of_tracks(self):
        return len(self._local_tracks)

    def get_local_tracks(self):
        return self._local_tracks
