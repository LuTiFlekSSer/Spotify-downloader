from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (ScrollArea, TitleLabel, BodyLabel, StrongBodyLabel,
                            PrimaryPushButton, InfoBar, InfoBarPosition)

from src.backend.spotify.session import SpotifySession
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.frontend.sub_windows.login_dialog.login_dialog import LoginDialog
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.utils import find_mega_parent
from src.version import __version__


class HomeWindow(ScrollArea):
    def __init__(self, name: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(name.replace(' ', '-'))
        self._locales: Locales = Locales()
        self._session: SpotifySession = SpotifySession()
        self._global_flags: GlobalFlags = GlobalFlags()

        self.__init_widget()
        self._refresh_status()

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

        self._vl_view.addSpacing(12)
        self._status_label: StrongBodyLabel = StrongBodyLabel('')
        self._vl_view.addWidget(self._status_label)

        row = QHBoxLayout()
        self._login_button: PrimaryPushButton = PrimaryPushButton(self._locales.get_string('login_button'))
        self._login_button.clicked.connect(self._on_login_clicked)
        row.addWidget(self._login_button)
        row.addStretch(1)
        self._vl_view.addLayout(row)

        self._vl_view.addStretch(1)
        self._vl_view.addWidget(BodyLabel(f'v{__version__} · PySide6 + Fluent'))

    def _refresh_status(self):
        if not self._session.is_configured():
            self._status_label.setText(self._locales.get_string('spotify_not_configured'))
            self._login_button.setText(self._locales.get_string('login_button'))
        elif self._session.is_authenticated():
            self._status_label.setText(self._locales.get_string('spotify_connected'))
            self._login_button.setText(self._locales.get_string('logout_button'))
        else:
            self._status_label.setText(self._locales.get_string('spotify_not_logged_in'))
            self._login_button.setText(self._locales.get_string('login_button'))

    def _on_login_clicked(self):
        hmi = find_mega_parent(self)

        if self._session.is_authenticated():
            self._session.logout()
            self._refresh_status()
            return

        dialog = LoginDialog(hmi)
        self._global_flags.modal_open.set()
        accepted = dialog.exec()
        self._global_flags.modal_open.clear()

        if accepted:
            InfoBar.success(
                title=self._locales.get_string('login_success'),
                content='',
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=hmi,
            )

        self._refresh_status()
