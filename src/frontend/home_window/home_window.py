import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, FluentIcon, InfoBar, InfoBarPosition

from src.backend.db.data_base import DataBase
from src.backend.spotify.session import SpotifySession
from src.frontend.home_window.banner import Banner
from src.frontend.home_window.status_card import StatusCardView
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.frontend.sub_windows.login_dialog.login_dialog import LoginDialog
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class HomeWindow(ScrollArea):
    def __init__(self, name: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(name.replace(' ', '-'))
        self._locales: Locales = Locales()
        self._db: DataBase = DataBase()
        self._session: SpotifySession = SpotifySession()
        self._global_flags: GlobalFlags = GlobalFlags()

        self.__init_widget()
        self._build_action_cards()
        self._refresh()

    def __init_widget(self):
        StyleSheet.HOME_WINDOW.apply(self)

        self._w_view = QWidget(self)
        self._w_view.setObjectName('w_view')
        self._vl_view = QVBoxLayout(self._w_view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self._w_view)
        self.setWidgetResizable(True)

        self._vl_view.setContentsMargins(36, 28, 36, 36)
        self._vl_view.setSpacing(36)
        self._vl_view.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._banner = Banner(self)
        self._status = StatusCardView(self._locales.get_string('status'), self)

        self._vl_view.addWidget(self._banner)
        self._vl_view.addWidget(self._status, 1)

    def _build_action_cards(self):
        s = self._locales.get_string
        cards = self._banner.card_view

        self._login_card = cards.add_card(
            FluentIcon.PEOPLE, s('login_button'), s('login_action_desc'), callback=self._on_login)
        cards.add_card(FluentIcon.SYNC, s('sync_action'), s('sync_action_desc'), callback=self._go_tracks)
        cards.add_card(FluentIcon.ALBUM, s('tracks_action'), s('tracks_action_desc'), callback=self._go_tracks)
        cards.add_card(FluentIcon.FOLDER, s('open_folder'), s('open_folder_desc'), callback=self._open_folder)
        cards.add_card(FluentIcon.GITHUB, s('github'), s('github_desc'), link_icon=True, callback=self._open_github)

    def _refresh(self):
        s = self._locales.get_string

        if self._session.is_authenticated():
            self._login_card.set_content(s('logout_button'), s('logout_action_desc'))
            spotify = (s('card_spotify'), s('spotify_connected'), True)
        else:
            self._login_card.set_content(s('login_button'), s('login_action_desc'))
            if self._session.is_configured():
                spotify = (s('card_spotify'), s('spotify_not_logged_in'), False)
            else:
                spotify = (s('card_spotify'), s('spotify_not_configured'), False)

        folder = self._db.get_setting('download_dir')
        folder_ok = bool(folder) and os.path.isdir(folder)
        folder_desc = folder if folder else s('folder_not_set')

        threads = self._db.get_setting('threads')

        self._status.set_cards([
            spotify,
            (s('card_folder'), folder_desc, folder_ok),
            (s('card_threads'), s('threads_value').format(n=threads), True),
        ])

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()

    # ---------- actions ----------
    def _on_login(self):
        hmi = find_mega_parent(self)

        if self._session.is_authenticated():
            self._session.logout()
            self._refresh()
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
        self._refresh()

    def _go_tracks(self):
        hmi = find_mega_parent(self)
        target = getattr(hmi, '_tracks_window', None)
        if target is None:
            return
        if hasattr(hmi, 'switchTo'):
            hmi.switchTo(target)
        else:
            hmi.stackedWidget.setCurrentWidget(target)

    def _open_folder(self):
        hmi = find_mega_parent(self)
        folder = self._db.get_setting('download_dir')
        if folder and os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            InfoBar.warning(
                title=self._locales.get_string('card_folder'),
                content=self._locales.get_string('folder_not_set'),
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=hmi,
            )

    @staticmethod
    def _open_github():
        QDesktopServices.openUrl(QUrl(Config.GITHUB_URL))
