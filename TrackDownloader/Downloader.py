__all__ = [
    'Downloader',
    'Status',
    'create_download_query'
]

import os
import time
import SettingsStorage
import requests
import eyed3
import enum
import SpotifyTracks
from urllib.parse import urlparse

eyed3.log.setLevel("ERROR")


class Status(enum.Enum):
    OK = 0
    API_ERR = 1
    GET_ERR = 2
    JPG_ERR = 3
    NF_ERR = 4
    TAG_ERR = 5
    CANCELLED = 6
    LINK_ERR = 7


def create_download_query(track, directory):
    separator = '\u29f8'

    track_info = {
        'id': track['id'],
        'name': track['title'],
        'artists': [aut.strip() for aut in track['artists'].split(',')],
        'album_name': track['album'],
        'release_date': track['releaseDate'][:4],
        'cover': track['cover']
    }

    return f"{track_info['name']} - {separator.join(track_info['artists'])}".translate(
        str.maketrans(SpotifyTracks.SpTracks.dict_for_replace)), directory, track_info


def _get_track_info(track_info):
    data = {
        'url': f'https://open.spotify.com/track/{track_info["id"]}',
    }

    response = requests.post('https://spotymp3.app/api/download-track', json=data)

    attempts = 0

    while attempts < 3 and not (response.status_code == 200 and 'file_url' in response.json()):
        response = requests.post('https://spotymp3.app/api/download-track', json=data).json()
        attempts += 1

    return response


def isfile_case_sensitive(path, name):
    if not os.path.exists(f'{path}\\{name}.mp3'):
        return False

    for file in os.listdir(path):
        if file == f'{name}.mp3':
            return True

    return False


class Downloader:
    metadata_headers = {
        'authority': 'api.spotifydown.com',
        'origin': 'https://spotifydown.com',
        'referer': 'https://spotifydown.com/'
    }

    def __init__(self, name, path, track_info, sync=False, lock=None):
        if not isinstance(name, str) or not isinstance(path, str) or not isinstance(track_info, dict):
            raise TypeError

        self._status = Status.OK

        self._settings = SettingsStorage.Settings()

        if not isfile_case_sensitive(path, name) and os.path.exists(f'{path}\\{name}.mp3'):
            if name not in self._settings.get_all_local_ignore_tracks() and sync:
                if lock is not None:
                    lock.acquire()

                self._settings.add_track_to_local_ignore(name)
                self._settings.save()

                if lock is not None:
                    lock.release()

            return

        if isfile_case_sensitive(path, name) and self._settings.get_setting('overwrite_tracks') == 'False':
            if lock is not None:
                lock.acquire()

            if (sync and
                    (self._settings.get_local_tracks_db()[name] == 'None' or self._settings.get_local_tracks_db()[
                        name] != track_info['id'])):
                self._settings.change_local_track_id(name, track_info['id'])

                self._settings.save()

            if lock is not None:
                lock.release()

            return

        self._download_track(name, path, track_info, sync, lock)

    def _download_track(self, name, path, track_info, sync, lock):
        try:
            response = _get_track_info(track_info)

            if not response.status_code == 200:
                self._status = Status.NF_ERR
                return False

            query = response.json()['file_url']

            try:
                attempts = 0
                track = requests.get(query)

                while attempts < 5 and track.status_code != 200:
                    track = requests.get(query)
                    attempts += 1

                if track.status_code != 200:
                    self._status = Status.GET_ERR
                    return False

                with open(f'{path}/{name}.mp3', 'wb') as file:
                    file.write(track.content)
            except Exception:
                self._status = Status.GET_ERR
                return False

        except Exception:
            self._status = Status.API_ERR
            return False

        track = eyed3.load(f'{path}/{name}.mp3')

        if track is None:
            self._status = Status.GET_ERR

            try:
                os.remove(f'{path}/{name}.mp3')
            except FileNotFoundError:
                pass

            return False

        try:
            track.tag.images.set(3, requests.get(track_info['cover']).content, 'image/jpeg')
        except Exception:
            self._status = Status.JPG_ERR

        track.tag.title = track_info['name']
        track.tag.artist = '/'.join(track_info['artists'])
        track.tag.album = track_info['album_name']

        try:
            track.tag.release_date = track_info['release_date']
        except ValueError:
            pass

        if sync:
            if lock is not None:
                lock.acquire()

            self._settings.add_track_to_local_tracks(name, track_info['id'])

            self._settings.save()

            if lock is not None:
                lock.release()

        attempts = 0

        while attempts < 3:
            try:
                track.tag.save()
                break
            except Exception:
                time.sleep(0.1)
                attempts += 1
        else:
            self._status = Status.TAG_ERR

        return True

    def status(self):
        return self._status
