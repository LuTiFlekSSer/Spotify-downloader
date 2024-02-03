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


def create_download_query(track, directory):
    separator = '\u29f8'

    track_info = {
        'id': track['id'],
        'name': track['title'],
        'artists': [aut.strip() for aut in track['artists'].split(',')],
        'album_name': track['album'],
        'release_date': track['releaseDate'][:4]
    }

    return f"{track_info['name']} - {separator.join(track_info['artists'])}".translate(str.maketrans(SpotifyTracks.SpTracks.dict_for_replace)), directory, track_info


def _get_track_info(track_info, method='download'):
    response = requests.get(f'https://api.spotifydown.com/{method}/{track_info["id"]}', headers=Downloader.headers).json()

    attempts = 0

    while attempts < 3 and not (response['success'] and 'link' in response):
        response = requests.get(f'https://api.spotifydown.com/{method}/{track_info["id"]}', headers=Downloader.headers).json()
        attempts += 1

    return response


class Downloader:
    headers = {
        'authority': 'api.spotifydown.com',
        'origin': 'https://spotifydown.com',
        'referer': 'https://spotifydown.com/'
    }

    def __init__(self, name, path, track_info, sync=False):
        if not isinstance(name, str) or not isinstance(path, str) or not isinstance(track_info, dict):
            raise TypeError

        self._status = Status.OK

        self._settings = SettingsStorage.Settings()
        if os.path.isfile(f'{path}\\{name}.mp3') and self._settings.get_setting('overwrite_tracks') == 'False':
            if (sync and
                    (self._settings.get_local_tracks_db()[name] == 'None' or self._settings.get_local_tracks_db()[name] != track_info['id'])):
                self._settings.change_local_track_id(name, track_info['id'])

                self._settings.save()

            return

        self._download_from_y2api(name, path, track_info, sync)

    def _download_from_y2api(self, name, path, track_info, sync):
        try:
            response = _get_track_info(track_info)

            if not response['success']:
                self._status = Status.NF_ERR
                return False

            domains = [
                'https://cdn1.tik.live/api/stream?',
                'https://cdn2.tik.live/api/stream?',
                'https://cdn3.tik.live/api/stream?'
            ]

            query = urlparse(response['link']).query

            try:
                for i, domain in enumerate(domains):
                    attempts = 0

                    header = Downloader.headers.copy()
                    header['authority'] = urlparse(domain).hostname

                    track = requests.get(domain + query, headers=header)

                    while attempts < 5 and track.status_code != 200:
                        track = requests.get(domain + query, headers=header)
                        attempts += 1

                    if track.status_code != 200:
                        if i == len(domains) - 1:
                            self._status = Status.GET_ERR
                            return False
                        else:
                            continue

                    with open(f'{path}/{name}.mp3', 'wb') as file:
                        file.write(track.content)
                        break

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
            track.tag.images.set(3, requests.get(response['metadata']['cover']).content, 'image/jpeg')
        except Exception:
            self._status = Status.JPG_ERR

        track.tag.title = track_info['name']
        track.tag.artist = '/'.join(track_info['artists'])
        track.tag.album = track_info['album_name']
        track.tag.release_date = track_info['release_date']
        if sync:
            self._settings.add_track_to_local_tracks(name, track_info['id'])

            self._settings.save()

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
