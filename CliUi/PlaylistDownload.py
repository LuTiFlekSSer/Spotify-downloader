import os
import requests
import win32com.client
import time
from urllib.parse import urlparse
import Utils
import TrackDownloader


class PlaylistDownload:
    def __init__(self):
        pass

    def playlist_download(self):
        os.system('cls')
        print(Utils.cyan('Загрузка треков из плейлиста\n'))

        print(Utils.yellow('Введи ссылку на плейлист'))
        link = Utils.g_input('> ')

        playlist_id = urlparse(link).path

        if '/' not in playlist_id:
            print(Utils.red('Некорректная ссылка'))
            time.sleep(1)
            return

        playlist_id = playlist_id[playlist_id.rfind('/') + 1:]

        try:
            directory = win32com.client.Dispatch('Shell.Application').BrowseForFolder(0, 'Выбери папку для сохранения треков', 16, "").Self.path
        except Exception:
            print(Utils.red('Загрузка отменена'))
            time.sleep(1)
            return

        playlist = []
        offset = 0

        try:
            while True:
                playlist_info = requests.get(f'https://api.spotifydown.com/trackList/playlist/{playlist_id}?offset={offset}', headers=TrackDownloader.Downloader.headers).json()

                if not playlist_info['success']:
                    print(Utils.red('Ошибка при загрузке информации о плейлисте'))
                    time.sleep(1)
                    return

                playlist += playlist_info['trackList']

                if playlist_info['nextOffset'] is None:
                    break

                offset = playlist_info['nextOffset']

        except Exception:
            print(Utils.red('Ошибка при работе с сcылкой'))
            time.sleep(1)
            return

        Utils.start_playlist_download(Utils.cyan('Загрузка треков из плейлиста\n'), [TrackDownloader.create_download_query(track, directory) for track in playlist])
