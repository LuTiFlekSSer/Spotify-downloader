from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics, QPixmap, QResizeEvent
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QStackedWidget, QLabel
from qfluentwidgets import (SimpleCardWidget, IconWidget, StrongBodyLabel, CaptionLabel,
                            ImageLabel, IndeterminateProgressRing, FluentIcon)

from src.backend.db.db_records import Track, TrackStatus, TRACK_STATUS_LOCALE
from src.frontend.tracks_window.cover_cache import cover_cache
from src.locales.locales import Locales
from src.utils.config import Config

_OK = ('#107C10', '#6CCB5F')
_ERR = ('#C42B1C', '#FF99A4')
_WARN = ('#9D5D00', '#E8B900')
_NEUTRAL = (Config.GRAY_COLOR_600, Config.GRAY_COLOR_300)
_ACCENT = ('#0067C0', '#4CC2FF')

# только FluentIcon (стандартный набор), без заливных кружков InfoBarIcon
_STATUS_STYLE = {
    TrackStatus.MISSING: (FluentIcon.MUSIC, _NEUTRAL),
    TrackStatus.QUEUED: (FluentIcon.HISTORY, _NEUTRAL),
    TrackStatus.DOWNLOADING: (FluentIcon.DOWNLOAD, _ACCENT),
    TrackStatus.DOWNLOADED: (FluentIcon.ACCEPT, _OK),
    TrackStatus.SKIPPED: (FluentIcon.ACCEPT, _OK),
    TrackStatus.DOWNLOAD_ERROR: (FluentIcon.CLOSE, _ERR),
    TrackStatus.NOT_FOUND: (FluentIcon.CLOSE, _ERR),
    TrackStatus.JPG_ERROR: (FluentIcon.PHOTO, _WARN),
    TrackStatus.TAG_ERROR: (FluentIcon.TAG, _WARN),
    TrackStatus.CANCELLED: (FluentIcon.CANCEL, _WARN),
    TrackStatus.LINK_ERROR: (FluentIcon.CLOSE, _ERR),
}
_DONE = (TrackStatus.DOWNLOADED, TrackStatus.SKIPPED)


def _centered(widget: QWidget) -> QWidget:
    box = QWidget()
    box.setFixedSize(40, 40)
    layout = QHBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignCenter)
    return box


class TrackRow(SimpleCardWidget):
    """Строка таблицы: слева иконка статуса / прогресс-ринг (загрузка) / обложка
    (после загрузки). Реализует set_data(track) для PagedListView."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(60)
        self._track: Track | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 16, 8)
        layout.setSpacing(14)

        self._visual = QStackedWidget(self)
        self._visual.setFixedSize(40, 40)
        self._iw_status = IconWidget()
        self._iw_status.setFixedSize(24, 24)
        self._cover = ImageLabel()
        self._cover.setFixedSize(40, 40)
        self._cover.setBorderRadius(6, 6, 6, 6)
        self._ring = IndeterminateProgressRing()
        self._ring.setFixedSize(26, 26)
        self._ring.setStrokeWidth(3)
        self._visual.addWidget(_centered(self._iw_status))   # 0
        self._visual.addWidget(self._cover)                  # 1
        self._visual.addWidget(_centered(self._ring))        # 2

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)
        self._l_title = StrongBodyLabel(self)
        self._l_artists = CaptionLabel(self)
        self._l_artists.setTextColor(QColor(Config.GRAY_COLOR_600), QColor(Config.GRAY_COLOR_300))
        text_box.addWidget(self._l_title)
        text_box.addWidget(self._l_artists)

        self._l_status = CaptionLabel(self)

        layout.addWidget(self._visual)
        layout.addLayout(text_box, 1)
        layout.addWidget(self._l_status, 0, Qt.AlignmentFlag.AlignRight)

        self._locales = Locales()
        cover_cache.loaded.connect(self._on_cover_loaded)

    def set_data(self, track: Track) -> None:
        self._track = track
        self._l_title.setText(self._elide(self._l_title, track.title))
        self._l_artists.setText(self._elide(self._l_artists, track.artists_str))

        icon, (light, dark) = _STATUS_STYLE.get(track.status, (FluentIcon.MUSIC, _NEUTRAL))
        self._l_status.setText(self._locales.get_string(TRACK_STATUS_LOCALE.get(track.status, 'state_missing')))
        self._l_status.setTextColor(QColor(light), QColor(dark))

        if track.status == TrackStatus.DOWNLOADING:
            self._visual.setCurrentIndex(2)
            self._ring.start()
            return

        self._ring.stop()

        if track.status in _DONE and track.cover:
            pixmap = cover_cache.get(track.cover)
            if pixmap is not None:
                self._cover.setImage(pixmap)
                self._cover.scaledToHeight(40)
                self._visual.setCurrentIndex(1)
                return
            cover_cache.request(track.cover)

        try:
            self._iw_status.setIcon(icon.colored(QColor(light), QColor(dark)))
        except Exception:
            self._iw_status.setIcon(icon)
        self._visual.setCurrentIndex(0)

    def _on_cover_loaded(self, url: str, pixmap: QPixmap) -> None:
        if (self._track is not None and self._track.cover == url
                and self._track.status in _DONE):
            self._cover.setImage(pixmap)
            self._cover.scaledToHeight(40)
            self._visual.setCurrentIndex(1)

    @staticmethod
    def _elide(label: QLabel, text: str) -> str:
        width = label.maximumWidth() if label.maximumWidth() < 16777215 else 360
        return QFontMetrics(label.font()).elidedText(text, Qt.TextElideMode.ElideRight, width)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._track is not None:
            self._l_title.setText(self._elide(self._l_title, self._track.title))
            self._l_artists.setText(self._elide(self._l_artists, self._track.artists_str))
