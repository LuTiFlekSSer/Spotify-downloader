__all__ = [
    'LcTracks'
]

from SettingsStorage import Settings
from os import listdir
from LocalTracks import Errors


class LcTracks:
    def __init__(self, directory=None):
        if directory is not None and not isinstance(directory, str):
            raise TypeError

        self._settings = Settings()
        self._directory = self._settings.get_setting('path_for_sync')

        if directory is not None:
            self._directory = directory
        elif self._directory == '':
            raise Errors.PathError

        self._local_tracks = set()

    def get_tracks_from_folder(self):
        tracks = listdir(self._directory)

        self._local_tracks.clear()

        local_tracks_db = self._settings.get_local_tracks_db()

        for i, track in enumerate(tracks):
            if track.endswith('.mp3'):
                if (name := track[:-4]) in local_tracks_db:
                    track_id = local_tracks_db[name]

                    local_tracks_db.pop(name)
                else:
                    track_id = 'None'

                    self._settings.add_track_to_local_tracks(name, track_id)

                self._local_tracks.add((track[:-4], track_id))

            yield i, len(tracks)

        for name in local_tracks_db:
            self._settings.delete_local_track(name)

        self._settings.save()

    def get_numbers_of_tracks(self):
        return len(self._local_tracks)

    def get_local_tracks(self):
        return self._local_tracks
