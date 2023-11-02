__all__ = [
    'Comparator'
]

import os
import SettingsStorage
import eyed3
import time


class Comparator:
    def __init__(self, local_tracks, spotify_tracks, tracks_info):
        if not isinstance(local_tracks, set) or not isinstance(spotify_tracks, set) or not isinstance(tracks_info, dict):
            raise TypeError

        self._local_tracks = local_tracks
        self._spotify_tracks = spotify_tracks
        self._tracks_info = tracks_info

        self._local_missing_tracks = None
        self._server_missing_tracks = None

        self._settings = SettingsStorage.Settings()

        self._refresh()

    def _get_missing_set_for_local_tracks(self):
        local_name_to_id = {name: track_id for name, track_id in self._local_tracks}

        server_id_to_name = {track_id: name for name, track_id in self._spotify_tracks}

        tracks = {name for name, _ in self._spotify_tracks}

        for name, track_id in local_name_to_id.items():
            if name in tracks:
                tracks.remove(name)
                server_id_to_name.pop(self._tracks_info[name]['id'])

                if track_id == 'None' or track_id != self._tracks_info[name]['id']:
                    self._settings.change_local_track_id(name, self._tracks_info[name]['id'])

            elif track_id != 'None' and track_id in server_id_to_name:
                tracks.remove(server_id_to_name[track_id])

                if name != server_id_to_name[track_id]:
                    attempts = 0

                    while attempts < 3:
                        try:
                            track = eyed3.load(f'{self._settings.get_setting("path_for_sync")}\\{name}.mp3')

                            track.tag.title = self._tracks_info[server_id_to_name[track_id]]['name']
                            track.tag.artist = '/'.join(self._tracks_info[server_id_to_name[track_id]]['artists'])

                            track.tag.save()

                            break
                        except Exception:
                            time.sleep(0.1)
                            attempts += 1

                    attempts = 0

                    while attempts < 3:
                        try:
                            os.rename(f'{self._settings.get_setting("path_for_sync")}\\{name}.mp3',
                                      f'{self._settings.get_setting("path_for_sync")}\\{server_id_to_name[track_id]}.mp3')

                            break
                        except Exception:
                            time.sleep(0.1)
                            attempts += 1

                    self._settings.delete_local_track(name)
                    self._settings.add_track_to_local_tracks(server_id_to_name[track_id], track_id)

                    self._local_tracks.remove((name, track_id))
                    self._local_tracks.add((server_id_to_name[track_id], track_id))

                server_id_to_name.pop(track_id)

        self._settings.save()

        return tracks

    def _get_missing_set_for_server_tracks(self):
        local_tracks = {name for name, _ in self._local_tracks}

        server_tracks = {name for name, _ in self._spotify_tracks}

        return local_tracks - server_tracks - self._settings.get_all_server_ignore_tracks()

    def _refresh(self):
        self._local_missing_tracks = {}

        for track in self._get_missing_set_for_local_tracks():
            self._local_missing_tracks[track] = self._tracks_info[track]

        self._server_missing_tracks = self._get_missing_set_for_server_tracks()

    def get_local_missing_tracks(self, refresh=False):
        if refresh:
            self._refresh()

        return self._local_missing_tracks

    def get_server_missing_tracks(self, refresh=False):
        if refresh:
            self._refresh()

        return sorted(self._server_missing_tracks)
