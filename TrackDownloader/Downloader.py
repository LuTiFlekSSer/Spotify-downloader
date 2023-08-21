__all__ = [
    'Downloader'
]

import requests
import eyed3


class Downloader:
    headers = {
        'authority': 'api.spotifydown.com',
        'origin': 'https://spotifydown.com',
        'referer': 'https://spotifydown.com/'
    }

    def __init__(self, name, path, track_info):
        try:
            response = requests.get(f'https://api.spotifydown.com/download/{track_info["id"]}', headers=Downloader.headers).json()

            attempts = 0

            while attempts < 3 and not response['success']:
                response = requests.get(f'https://api.spotifydown.com/download/{track_info["id"]}', headers=Downloader.headers).json()
                attempts += 1

            if not response['success']:
                print(f'Трек {name} не найден')
                return

            try:
                track = requests.get(response['link']).content

                with open(f'{path}/{name}.mp3', 'wb') as file:
                    file.write(track)

            except Exception:
                print(f'Ошибка при загрузке трека: {name}')
                return

        except Exception:
            print(f'Ошибка получения данных о треке: {name}')
            return

        track = eyed3.load(f'{path}/{name}.mp3')

        try:
            track.tag.images.set(3, requests.get(response['metadata']['cover']).content, 'image/jpeg')
        except Exception:
            print(f'Ошибка изменения обложки трека: {name}')

        track.tag.title = track_info['name']
        track.tag.artist = '/'.join(track_info['artists'])
        track.tag.album = track_info['album_name']
        track.tag.release_date = track_info['release_date']

        track.tag.save()
