import time

from PySide6.QtCore import QThread, Signal

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track, TrackStatus
from src.backend.spotify.constants import build_filename
from src.backend.spotify.session import SpotifySession


class LikedTracksFetcher(QThread):
    """Фоновый загрузчик «любимых» треков из Spotify (spotipy).

    Заменяет старый busy-wait `while is_alive(): self.update()` нормальным
    QThread + сигналами. Постранично (limit=50), последовательно — это убирает
    старый баг прогресса >100% и не требует своего пула."""

    sig_progress: Signal = Signal(int, int)        # (получено, всего)
    sig_finished: Signal = Signal(list)            # list[Track]
    sig_error: Signal = Signal(str)

    _LIMIT = 50
    _ATTEMPTS = 4

    def __init__(self, session: SpotifySession, parent=None):
        super().__init__(parent)
        self._session = session
        self._db = DataBase()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            client = self._session.get_client()
            total = client.current_user_saved_tracks(limit=1)['total']
            ignore = self._db.get_local_ignore()

            tracks: list[Track] = []
            for offset in range(0, total, self._LIMIT):
                if self._stop:
                    break

                for item in self._fetch_page(client, offset):
                    raw = item.get('track')
                    if not raw or not raw.get('id'):
                        continue

                    artists = [a['name'] for a in raw['artists']]
                    name = build_filename(raw['name'], artists)
                    if name in ignore:
                        continue

                    images = raw['album'].get('images') or []
                    tracks.append(Track(
                        id=raw['id'],
                        title=raw['name'],
                        artists=artists,
                        album=raw['album'].get('name', ''),
                        release_date=(raw['album'].get('release_date') or '')[:4],
                        cover=images[0]['url'] if images else '',
                        status=TrackStatus.MISSING,
                    ))

                self.sig_progress.emit(min(offset + self._LIMIT, total), total)

            self.sig_finished.emit(tracks)
        except Exception as e:
            self.sig_error.emit(str(e))

    def _fetch_page(self, client, offset) -> list:
        last_exc = None
        for attempt in range(self._ATTEMPTS):
            try:
                return client.current_user_saved_tracks(limit=self._LIMIT, offset=offset)['items']
            except Exception as e:
                last_exc = e
                time.sleep(0.5)
        raise last_exc
