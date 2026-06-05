from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track
from src.backend.library.comparator import Comparator
from src.backend.library.scanner import LocalScanner
from src.backend.spotidl.api_client import ApiClient


def parse_spotify_id(url: str) -> str:
    """Последний сегмент пути ссылки Spotify (id трека/плейлиста)."""
    segments = [s for s in urlparse(url.strip()).path.split('/') if s]
    return segments[-1] if segments else ''


class ScanCompareWorker(QThread):
    """Сканирует локальную папку и сравнивает с любимыми Spotify."""

    sig_progress = Signal(int, int)
    sig_finished = Signal(object, object)   # server_missing: list[str], local_missing: list[Track]
    sig_error = Signal(str)

    def __init__(self, directory: str, spotify_by_name: dict, parent=None):
        super().__init__(parent)
        self._directory = directory
        self._spotify = spotify_by_name
        self._db = DataBase()

    def run(self):
        try:
            local = LocalScanner(self._directory, self._db).scan(
                progress=lambda i, t: self.sig_progress.emit(i, t))
            server_missing, local_missing = Comparator(
                local, self._spotify, self._directory, self._db).compute()
            self.sig_finished.emit(server_missing, local_missing)
        except Exception as e:
            self.sig_error.emit(str(e))


class PlaylistEnumerateWorker(QThread):
    """Постранично собирает все треки плейлиста через spotidownloader."""

    sig_progress = Signal(int)
    sig_finished = Signal(object)           # list[Track]
    sig_error = Signal(str)

    def __init__(self, api: ApiClient, playlist_id: str, parent=None):
        super().__init__(parent)
        self._api = api
        self._playlist_id = playlist_id

    def run(self):
        try:
            raw = self._api.all_tracks(self._playlist_id, 'playlist',
                                       progress=lambda n: self.sig_progress.emit(n))
            self.sig_finished.emit([Track.from_api(t) for t in raw])
        except Exception as e:
            self.sig_error.emit(str(e))


class TrackResolveWorker(QThread):
    """Резолвит один трек по ссылке (метаданные для отображения)."""

    sig_finished = Signal(object)           # Track
    sig_error = Signal(str)

    def __init__(self, api: ApiClient, track_id: str, parent=None):
        super().__init__(parent)
        self._api = api
        self._track_id = track_id

    def run(self):
        try:
            data = self._api.metadata('track', self._track_id)
            data = dict(data)
            data['id'] = self._track_id
            self.sig_finished.emit(Track.from_api(data))
        except Exception as e:
            self.sig_error.emit(str(e))
