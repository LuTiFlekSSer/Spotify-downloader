from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, TitleLabel, BodyLabel

from src.frontend.style_sheets.style_sheets import StyleSheet
from src.locales.locales import Locales
from src.version import __version__


class HomeWindow(ScrollArea):
    def __init__(self, name: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(name.replace(' ', '-'))
        self._locales: Locales = Locales()

        self.__init_widget()

    def __init_widget(self):
        StyleSheet.HOME_WINDOW.apply(self)

        self._w_view: QWidget = QWidget(self)
        self._w_view.setObjectName('w_view')
        self._vl_view: QVBoxLayout = QVBoxLayout(self._w_view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self._w_view)
        self.setWidgetResizable(True)

        self._vl_view.setContentsMargins(28, 28, 28, 28)
        self._vl_view.setSpacing(12)
        self._vl_view.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._vl_view.addWidget(TitleLabel('Spotify Downloader'))
        self._vl_view.addWidget(BodyLabel(self._locales.get_string('home_subtitle')))
        self._vl_view.addWidget(BodyLabel(f'v{__version__} · PySide6 + Fluent'))
