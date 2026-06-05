import requests
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt
from PySide6.QtGui import QImage, QPixmap


class _FetchSignals(QObject):
    loaded = Signal(str, object)   # url, QPixmap


class _FetchTask(QRunnable):
    def __init__(self, url: str, signals: _FetchSignals):
        super().__init__()
        self._url = url
        self._signals = signals

    def run(self):
        try:
            data = requests.get(self._url, timeout=15).content
            pixmap = QPixmap.fromImage(QImage.fromData(data))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                self._signals.loaded.emit(self._url, pixmap)
        except Exception:
            pass


class CoverCache(QObject):
    """Асинхронная загрузка обложек по URL с кэшем (QThreadPool).
    loaded(url, QPixmap) приходит в GUI-поток."""

    loaded = Signal(str, object)

    def __init__(self):
        super().__init__()
        self._cache: dict[str, QPixmap] = {}
        self._pending: set[str] = set()
        self._pool = QThreadPool.globalInstance()
        self._signals = _FetchSignals()
        self._signals.loaded.connect(self._on_loaded)

    def get(self, url: str):
        return self._cache.get(url)

    def request(self, url: str):
        if not url or url in self._cache or url in self._pending:
            return
        self._pending.add(url)
        self._pool.start(_FetchTask(url, self._signals))

    def _on_loaded(self, url: str, pixmap: QPixmap):
        self._cache[url] = pixmap
        self._pending.discard(url)
        self.loaded.emit(url, pixmap)


cover_cache = CoverCache()
