from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (SimpleCardWidget, IconWidget, StrongBodyLabel, CaptionLabel,
                            FluentIcon, InfoBarIcon)

from src.backend.db.db_records import Track, TrackStatus, TRACK_STATUS_LOCALE
from src.locales.locales import Locales
from src.utils.config import Config

# статус -> (иконка, цвет-светлый, цвет-тёмный)
_OK = ('#107C10', '#6CCB5F')
_ERR = ('#C42B1C', '#FF99A4')
_WARN = ('#9D5D00', '#FCE100')
_NEUTRAL = (Config.GRAY_COLOR_600, Config.GRAY_COLOR_300)
_ACCENT = ('#0067C0', '#4CC2FF')

_STATUS_STYLE = {
    TrackStatus.MISSING: (FluentIcon.MUSIC, _NEUTRAL),
    TrackStatus.QUEUED: (FluentIcon.HISTORY, _NEUTRAL),
    TrackStatus.DOWNLOADING: (FluentIcon.DOWNLOAD, _ACCENT),
    TrackStatus.DOWNLOADED: (InfoBarIcon.SUCCESS, _OK),
    TrackStatus.SKIPPED: (InfoBarIcon.SUCCESS, _OK),
    TrackStatus.DOWNLOAD_ERROR: (InfoBarIcon.ERROR, _ERR),
    TrackStatus.NOT_FOUND: (InfoBarIcon.ERROR, _ERR),
    TrackStatus.JPG_ERROR: (InfoBarIcon.WARNING, _WARN),
    TrackStatus.TAG_ERROR: (InfoBarIcon.WARNING, _WARN),
    TrackStatus.CANCELLED: (InfoBarIcon.WARNING, _WARN),
    TrackStatus.LINK_ERROR: (InfoBarIcon.ERROR, _ERR),
}


class TrackRow(SimpleCardWidget):
    """Строка таблицы треков. Реализует set_data(track) для PagedListView."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self._track: Track | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(14)

        self._iw_status = IconWidget(self)
        self._iw_status.setFixedSize(22, 22)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)
        self._l_title = StrongBodyLabel(self)
        self._l_artists = CaptionLabel(self)
        self._l_artists.setTextColor(QColor(Config.GRAY_COLOR_600), QColor(Config.GRAY_COLOR_300))
        text_box.addWidget(self._l_title)
        text_box.addWidget(self._l_artists)

        self._l_status = CaptionLabel(self)

        layout.addWidget(self._iw_status)
        layout.addLayout(text_box, 1)
        layout.addWidget(self._l_status, 0, Qt.AlignmentFlag.AlignRight)

        self._locales = Locales()

    def set_data(self, track: Track):
        self._track = track
        self._l_title.setText(self._elide(self._l_title, track.title))
        self._l_artists.setText(self._elide(self._l_artists, track.artists_str))

        icon, (light, dark) = _STATUS_STYLE.get(track.status, (FluentIcon.MUSIC, _NEUTRAL))
        try:
            self._iw_status.setIcon(icon.colored(QColor(light), QColor(dark)))
        except Exception:
            self._iw_status.setIcon(icon)
        self._l_status.setText(self._locales.get_string(TRACK_STATUS_LOCALE.get(track.status, 'state_missing')))
        self._l_status.setTextColor(QColor(light), QColor(dark))

    @staticmethod
    def _elide(label, text: str) -> str:
        width = label.maximumWidth() if label.maximumWidth() < 16777215 else 360
        return QFontMetrics(label.font()).elidedText(text, Qt.TextElideMode.ElideRight, width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._track is not None:
            self._l_title.setText(self._elide(self._l_title, self._track.title))
            self._l_artists.setText(self._elide(self._l_artists, self._track.artists_str))
