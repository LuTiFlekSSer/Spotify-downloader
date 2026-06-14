from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, LargeTitleLabel

from src.frontend.settings_window.settings import DownloadSettings, AccountSettings, AppSettings
from src.frontend.settings_window.spotify_config import spotify_config
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.locales.locales import Locales
from src.utils.config import Config


class SettingsWindow(ScrollArea):
    def __init__(self, name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName(name.replace(' ', '-'))
        self._locales = Locales()
        # spotify_config грузится на импорте (до определения языка) — пере-синхронизируем
        # с DataBase здесь, чтобы карточки (особенно язык) отражали актуальные значения.
        spotify_config.reload()

        self.__init_widgets()

    def __init_widgets(self) -> None:
        StyleSheet.SETTINGS_WINDOW.apply(self)

        self._w_view = QWidget(self)
        self._w_view.setObjectName('w_view')
        self._vl_view = QVBoxLayout(self._w_view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self._w_view)
        self.setWidgetResizable(True)

        self._vl_view.setContentsMargins(36, 28, 36, 36)
        self._vl_view.setSpacing(0)
        self._vl_view.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._l_title = LargeTitleLabel(self)
        self._l_title.setText(self._locales.get_string('settings'))
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._download = DownloadSettings(self)
        self._account = AccountSettings(self)
        self._app = AppSettings(self)

        self._vl_view.addWidget(self._l_title)
        self._vl_view.addSpacing(28)
        self._vl_view.addWidget(self._download)
        self._vl_view.addSpacing(20)
        self._vl_view.addWidget(self._account)
        self._vl_view.addSpacing(20)
        self._vl_view.addWidget(self._app)
