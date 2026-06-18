import os
import time

import eyed3

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track, TrackStatus
from src.backend.spotidl.api_client import ApiClient
from src.backend.spotify.constants import build_filename

eyed3.log.setLevel('ERROR')


class Downloader:
    """Скачивает один трек: резолвит mp3-ссылку через spotidownloader, пишет файл,
    проставляет ID3-теги (title/artist/album/release_date/cover) через eyed3.
    Логика skip/overwrite/sync-DB перенесена из старого TrackDownloader.Downloader,
    но без внешнего лока — новая DataBase потокобезопасна сама."""

    def __init__(self, api: ApiClient, db: DataBase | None = None) -> None:
        self._api = api
        self._db = db or DataBase()

    def download(self, track: Track, directory: str, sync: bool = False) -> TrackStatus:
        name = build_filename(track.title, track.artists)
        path = os.path.join(directory, f'{name}.mp3')
        overwrite = self._db.get_setting('overwrite_tracks') == 'True'

        # уже есть на диске и перезапись выключена -> пропускаем (в sync обновляем карту)
        if os.path.exists(path) and not overwrite:
            if sync:
                self._db.set_library_track(name, track.id)
            return TrackStatus.SKIPPED

        # 1) ссылка на mp3
        try:
            data = self._api.download_link(track.id)
        except Exception:
            return TrackStatus.DOWNLOAD_ERROR

        link = data.get('link')
        if not data.get('success') or not link:
            return TrackStatus.NOT_FOUND

        # 2) байты mp3
        try:
            content = self._api.fetch_bytes(link)
            with open(path, 'wb') as file:
                file.write(content)
        except Exception:
            return TrackStatus.DOWNLOAD_ERROR

        # 3) теги
        status = self._tag(path, track)

        if status not in (TrackStatus.DOWNLOAD_ERROR, TrackStatus.NOT_FOUND) and sync:
            self._db.set_library_track(name, track.id)

        return status

    def _tag(self, path: str, track: Track) -> TrackStatus:
        audio = eyed3.load(path)
        if audio is None:
            try:
                os.remove(path)
            except OSError:
                pass
            return TrackStatus.DOWNLOAD_ERROR

        if audio.tag is None:
            audio.initTag()

        status = TrackStatus.DOWNLOADED

        if track.cover:
            try:
                cover = self._api.fetch_bytes(track.cover, timeout=30)
                audio.tag.images.set(3, cover, 'image/jpeg')
            except Exception:
                status = TrackStatus.JPG_ERROR

        audio.tag.title = track.title
        audio.tag.artist = '/'.join(track.artists)
        audio.tag.album = track.album
        try:
            audio.tag.release_date = track.release_date
        except (ValueError, TypeError):
            pass

        for _ in range(3):
            try:
                audio.tag.save()
                break
            except Exception:
                time.sleep(0.1)
        else:
            return TrackStatus.TAG_ERROR

        return status
