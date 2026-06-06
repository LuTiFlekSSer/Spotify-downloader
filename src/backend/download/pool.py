import os
import threading
from concurrent.futures import ThreadPoolExecutor, CancelledError, as_completed, Future
from typing import Iterable

from PySide6.QtCore import QObject, Signal

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track, TrackStatus
from src.backend.download.downloader import Downloader
from src.backend.spotidl.api_client import ApiClient
from src.backend.spotidl.session import SpotiSession
from src.global_flags import GlobalFlags
from src.utils.singleton import Singleton


class DownloaderPool(metaclass=Singleton):
    """Пул загрузки треков. download() атомарно проверяет/занимает движок и
    запускает контроллер-поток, который раздаёт задачи в ThreadPoolExecutor
    (size = настройка 'threads') и шлёт сигналы в UI.

    Сигналы (queued, доставляются в GUI-поток):
      sig_track_status(track_id, TrackStatus) — статус по треку (в т.ч. DOWNLOADING)
      sig_progress(done, total)               — общий прогресс
      sig_finished(summary)                   — {TrackStatus: count}
    """

    class Events(QObject):
        sig_track_status = Signal(str, object)
        sig_progress = Signal(int, int)
        sig_finished = Signal(object)

    events = Events()

    def __init__(self) -> None:
        self._db = DataBase()
        self._downloader = Downloader(ApiClient(SpotiSession()), self._db)
        self._global_flags = GlobalFlags()

        self._lock = threading.Lock()
        self._cancel = False
        self._futures: dict[Future[TrackStatus], Track] = {}
        self._done = 0
        self._total = 0

    def is_running(self) -> bool:
        return self._global_flags.is_running.is_set()

    def download(self, tracks: Iterable[Track], directory: str, sync: bool = False) -> bool:
        tracks = list(tracks)
        # атомарный test-and-set: занимаем движок ДО старта потока, чтобы два
        # параллельных download() не пересеклись на общем состоянии синглтона.
        with self._lock:
            if self._global_flags.is_running.is_set():
                return False
            self._global_flags.is_running.set()
            self._cancel = False
            self._futures = {}
            self._done = 0
            self._total = len(tracks)

        threading.Thread(
            target=self._run, args=(tracks, directory, sync),
            daemon=True, name='DownloaderPool').start()
        return True

    def stop(self) -> None:
        with self._lock:
            self._cancel = True
            for future in self._futures:
                if not future.running():
                    future.cancel()

    def _run(self, tracks: list[Track], directory: str, sync: bool) -> None:
        summary: dict[TrackStatus, int] = {}
        try:
            pool = ThreadPoolExecutor(self._resolve_threads())
            try:
                with self._lock:
                    for track in tracks:
                        future = pool.submit(self._download_one, track, directory, sync)
                        self._futures[future] = track
                    snapshot = dict(self._futures)

                for future in as_completed(snapshot):
                    track = snapshot[future]
                    try:
                        status = future.result()
                    except CancelledError:
                        status = TrackStatus.CANCELLED
                    except Exception:
                        status = TrackStatus.DOWNLOAD_ERROR

                    self.events.sig_track_status.emit(track.id, status)
                    with self._lock:
                        self._done += 1
                        summary[status] = summary.get(status, 0) + 1
                        done, total = self._done, self._total
                    self.events.sig_progress.emit(done, total)
            finally:
                pool.shutdown(wait=True)
        finally:
            with self._lock:
                self._futures = {}
            self._global_flags.is_running.clear()
            self.events.sig_finished.emit(summary)

    def _download_one(self, track: Track, directory: str, sync: bool) -> TrackStatus:
        with self._lock:
            cancelled = self._cancel
        if cancelled:
            return TrackStatus.CANCELLED

        self.events.sig_track_status.emit(track.id, TrackStatus.DOWNLOADING)
        return self._downloader.download(track, directory, sync)

    def _resolve_threads(self) -> int:
        try:
            return max(1, int(self._db.get_setting('threads')))
        except (ValueError, TypeError):
            return max(1, os.cpu_count() or 4)
