from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import (MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit, PasswordLineEdit,
                            HyperlinkLabel, TeachingTipView, PopupTeachingTip, InfoBarIcon)

from src.backend.spotify import errors
from src.backend.spotify.session import SpotifySession
from src.locales.locales import Locales


class LoginDialog(MessageBoxBase):
    """Двухшаговый мастер входа в Spotify (MessageBoxBase + QStackedWidget):
    шаг 0 — ввод client_id/secret/redirect_uri; шаг 1 — вставка redirect-URL.
    Логика шагов — в validate(): вернуть False оставляет диалог открытым."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._locales: Locales = Locales()
        self._session: SpotifySession = SpotifySession()

        self.widget.setMinimumWidth(520)

        self._title = SubtitleLabel(self._locales.get_string('login_title'))

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_credentials_page())
        self._stack.addWidget(self._build_code_page())

        self.viewLayout.addWidget(self._title)
        self.viewLayout.addSpacing(self.viewLayout.spacing())
        self.viewLayout.addWidget(self._stack)

        self.yesButton.setText(self._locales.get_string('next'))
        self.cancelButton.setText(self._locales.get_string('cancel'))

    def _build_credentials_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self._cid = LineEdit()
        self._cid.setText(self._session._db.get_setting('client_id'))
        self._secret = PasswordLineEdit()
        self._secret.setText(self._session._db.get_setting('client_secret'))
        self._uri = LineEdit()
        self._uri.setText(self._session._db.get_setting('redirect_uri'))

        layout.addWidget(BodyLabel('Client ID:'))
        layout.addWidget(self._cid)
        layout.addWidget(BodyLabel('Client Secret:'))
        layout.addWidget(self._secret)
        layout.addWidget(BodyLabel('Redirect URI:'))
        layout.addWidget(self._uri)
        return page

    def _build_code_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self._desc = BodyLabel(self._locales.get_string('code_description'))
        self._desc.setWordWrap(True)
        self._link = HyperlinkLabel(QUrl('https://accounts.spotify.com'), 'URL', self)
        self._url_edit = LineEdit()
        self._url_edit.setPlaceholderText('URL')

        layout.addWidget(self._desc)
        layout.addWidget(self._link)
        layout.addWidget(BodyLabel('URL:'))
        layout.addWidget(self._url_edit)
        return page

    # ---------- MessageBoxBase hook ----------
    def validate(self) -> bool:
        if self._stack.currentIndex() == 0:
            return self._advance_to_code()
        return self._do_login()

    def _advance_to_code(self) -> bool:
        cid = self._cid.text().strip()
        secret = self._secret.text().strip()
        uri = self._uri.text().strip()

        if not (cid and secret and uri):
            self._error_tip(self._cid, self._locales.get_string('login_error'))
            return False

        try:
            self._session.set_credentials(cid, secret, uri)
            url = self._session.get_authorization_url()
        except errors._SpotifyError:
            self._error_tip(self._cid, self._locales.get_string('authorization_error'))
            return False

        QGuiApplication.clipboard().setText(url)
        self._link.setUrl(QUrl(url))
        self._link.setText(url if len(url) <= 64 else url[:61] + '...')

        self._stack.setCurrentIndex(1)
        return False   # остаёмся открытыми на шаге кода

    def _do_login(self) -> bool:
        try:
            self._session.complete_login(self._url_edit.text().strip())
            return True
        except errors.AuthUrlError:
            self._error_tip(self._url_edit, self._locales.get_string('url_code_error'))
        except errors.AuthError:
            self._error_tip(self._url_edit, self._locales.get_string('authorization_error'))
        except Exception:
            self._error_tip(self._url_edit, self._locales.get_string('authorization_error'))
        return False

    def _error_tip(self, target, content: str):
        view = TeachingTipView(
            title=self._locales.get_string('error'),
            content=content,
            icon=InfoBarIcon.ERROR,
            parent=self,
        )
        tip = PopupTeachingTip.make(view=view, target=target, duration=3000, parent=self)
        view.closed.connect(tip.close)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.yesButton.clicked.emit()
            return
        super().keyPressEvent(event)
