__all__ = [
    'Downloader',
    'Status'
]

import requests
import eyed3
import enum


class Status(enum.Enum):
    OK = 0
    API_ERR = 1
    GET_ERR = 2
    JPG_ERR = 3
    NF_ERR = 4


class Downloader:
    headers = {
        'authority': 'api.spotifydown.com',
        'origin': 'https://spotifydown.com',
        'referer': 'https://spotifydown.com/'
    }

    def __init__(self, name, path, track_info):
        if not isinstance(name, str) or not isinstance(path, str) or not isinstance(track_info, dict):
            raise TypeError

        self._status = Status.OK

        try:
            response = requests.get(f'https://api.spotifydown.com/download/{track_info["id"]}', headers=Downloader.headers).json()

            attempts = 0

            while attempts < 3 and not response['success']:
                response = requests.get(f'https://api.spotifydown.com/download/{track_info["id"]}', headers=Downloader.headers).json()
                attempts += 1

            if not response['success']:
                # print(f'Трек {name} не найден')
                self._status = Status.NF_ERR
                return

            try:
                track = requests.get(response['link']).content

                attempts = 0

                while attempts < 5 and track.startswith(b'{"error":true'):
                    track = requests.get(response['link']).content
                    attempts += 1

                if track.startswith(b'{"error":true'):
                    # print(f'Ошибка при загрузке трека: {name}')
                    self._status = Status.GET_ERR
                    return

                with open(f'{path}/{name}.mp3', 'wb') as file:
                    file.write(track)

            except Exception:
                # print(f'Ошибка при загрузке трека: {name}')
                self._status = Status.GET_ERR
                return

        except Exception:
            # print(f'Ошибка получения данных о треке: {name}')
            self._status = Status.API_ERR
            return

        track = eyed3.load(f'{path}/{name}.mp3')

        try:
            track.tag.images.set(3, requests.get(response['metadata']['cover']).content, 'image/jpeg')
        except Exception:
            self._status = Status.JPG_ERR
            # print(f'Ошибка изменения обложки трека: {name}')

        track.tag.title = track_info['name']
        track.tag.artist = '/'.join(track_info['artists'])
        track.tag.album = track_info['album_name']
        track.tag.release_date = track_info['release_date']

        track.tag.save()

    def status(self):
        return self._status
