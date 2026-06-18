from typing import Any, Callable, Optional, Union

from PySide6.QtCore import Qt, QUrl, QObject
from PySide6.QtGui import QDesktopServices, QColor, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (TitleLabel, FluentIcon, FluentIconBase, PrimaryPushSettingCard, PushSettingCard,
                            SwitchSettingCard, ComboBoxSettingCard, SettingCard, SpinBox, MessageBox,
                            InfoBar, InfoBarPosition, setTheme, Theme, setCustomStyleSheet,
                            MessageBoxBase, SubtitleLabel, BodyLabel, ScrollArea, SimpleCardWidget,
                            TransparentToolButton, PushButton)
from qfluentwidgets import RangeConfigItem

from src.backend.db.data_base import DataBase
from src.backend.spotify.session import SpotifySession
from src.frontend.settings_window.spotify_config import spotify_config
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent
from src.version import __version__
from src.backend.updater.updater import Updater, ReleaseInfo
from src.backend.updater.workers import UpdateCheckWorker
from src.frontend.sub_windows.update_dialog.update_dialog import UpdateDownloadDialog

_QSS_LIGHT = f'#setting-content{{color: {Config.GRAY_COLOR_700}; font-size: 12px;}}'
_QSS_DARK = f'#setting-content{{color: {Config.GRAY_COLOR_200}; font-size: 12px;}}'


def _dim(card: SettingCard) -> None:
    card.contentLabel.setObjectName('setting-content')
    setCustomStyleSheet(card, _QSS_LIGHT, _QSS_DARK)


class CustomSwitchingCard(SwitchSettingCard):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._locales = Locales()          # до super(): база зовёт setValue() в __init__
        super().__init__(*args, **kwargs)
        self._update_text(self.switchButton.isChecked())

    def setValue(self, is_checked: bool) -> None:
        if self.configItem:
            spotify_config.set(self.configItem, is_checked)
        self.switchButton.setChecked(is_checked)
        self._update_text(is_checked)

    def _update_text(self, on: bool) -> None:
        self.switchButton.setText(
            self._locales.get_string('turn_on') if on else self._locales.get_string('turn_off'))


class CustomComboBoxSettingCard(ComboBoxSettingCard):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._locales = Locales()          # до super(): на случай ранних вызовов
        super().__init__(*args, **kwargs)

    def setValue(self, value: str) -> None:
        if value not in self.optionToText:
            return
        self.comboBox.setCurrentText(self.optionToText[value])
        spotify_config.set(self.configItem, value)

        if self.configItem is spotify_config.app_language:
            InfoBar.info(
                title=self._locales.get_string('notification'),
                content=self._locales.get_string('restart_notification'),
                orient=Qt.Orientation.Horizontal, position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000, isClosable=False, parent=find_mega_parent(self))
        elif self.configItem is spotify_config.app_theme:
            setTheme(getattr(Theme, value))

    def _onCurrentIndexChanged(self, index: int) -> None:
        spotify_config.set(self.configItem, self.comboBox.itemData(index))


class SpinBoxSettingCard(SettingCard):
    def __init__(self, config_item: RangeConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(icon, title, content, parent)
        self.configItem = config_item
        self.spin_box = SpinBox(self)
        self.spin_box.setRange(*config_item.range)
        self.spin_box.setValue(config_item.value)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.spin_box, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.spin_box.editingFinished.connect(lambda: spotify_config.set(self.configItem, self.spin_box.value()))


class FolderSettingCard(PushSettingCard):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self._locales = Locales()
        current = spotify_config.download_dir.value or self._locales.get_string('folder_not_set')
        super().__init__(self._locales.get_string('choose_folder'), FluentIcon.FOLDER,
                         self._locales.get_string('download_folder'), current, parent)
        self.clicked.connect(self._choose)

    def _choose(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, self._locales.get_string('choose_folder'), spotify_config.download_dir.value or '')
        if directory:
            spotify_config.set(spotify_config.download_dir, directory)
            self.setContent(directory)


class ClearAccountCard(PushSettingCard):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self._locales = Locales()
        super().__init__(self._locales.get_string('clear_account_btn'), FluentIcon.DELETE,
                         self._locales.get_string('clear_account'),
                         self._locales.get_string('clear_account_desc'), parent)
        self._session = SpotifySession()
        self._db = DataBase()
        self.clicked.connect(self._clear)

    def _clear(self) -> None:
        hmi = find_mega_parent(self)
        box = MessageBox(self._locales.get_string('clear_account'),
                         self._locales.get_string('clear_account_confirm'), hmi)
        if not box.exec():
            return
        self._session.logout()
        for key in ('client_id', 'client_secret', 'redirect_uri'):
            self._db.set_setting(key, '')
        InfoBar.success(title=self._locales.get_string('account_cleared'), content='',
                        position=InfoBarPosition.BOTTOM_RIGHT, duration=3000, parent=hmi)


class AboutUpdateCard(PrimaryPushSettingCard):
    """Карточка «О программе» с реальной проверкой обновлений на GitHub."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self._locales = Locales()
        super().__init__(
            self._locales.get_string('check_for_updates'),
            FluentIcon.INFO.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            self._locales.get_string('about'),
            self._locales.get_string('about_desc').format(version=__version__), parent)
        self._updater = Updater()
        self._checker: Optional[UpdateCheckWorker] = None
        self.clicked.connect(self._check)

    def _check(self) -> None:
        if self._checker is not None and self._checker.isRunning():
            return
        self.button.setEnabled(False)
        self.button.setText(self._locales.get_string('checking'))
        self._checker = UpdateCheckWorker(self._updater, self)
        self._checker.sig_result.connect(self._on_result)
        self._checker.sig_error.connect(self._on_error)
        self._checker.finished.connect(self._restore)
        self._checker.start()

    def _restore(self) -> None:
        self.button.setEnabled(True)
        self.button.setText(self._locales.get_string('check_for_updates'))

    def _on_error(self, *_: str) -> None:
        InfoBar.error(title=self._locales.get_string('error'),
                      content=self._locales.get_string('update_check_error'),
                      position=InfoBarPosition.BOTTOM_RIGHT, duration=4000, parent=find_mega_parent(self))

    def _on_result(self, release: Optional[ReleaseInfo]) -> None:
        hmi = find_mega_parent(self)
        if release is None:
            InfoBar.success(title=self._locales.get_string('check'),
                            content=self._locales.get_string('last_update_installed'),
                            position=InfoBarPosition.BOTTOM_RIGHT, duration=4000, parent=hmi)
            return

        box = MessageBox(
            self._locales.get_string('update_available').format(version=release.version),
            self._locales.get_string('update_title'), hmi)
        box.yesButton.setText(self._locales.get_string('yes'))
        box.cancelButton.setText(self._locales.get_string('no'))
        if not box.exec():
            return

        if not self._updater.is_frozen():
            # из исходников самоподмена невозможна — открываем страницу релизов
            QDesktopServices.openUrl(QUrl(Config.GITHUB_RELEASES_HTML))
            return

        UpdateDownloadDialog(self._updater, hmi).exec()


class IgnoreListDialog(MessageBoxBase):
    """Просмотр и редактирование игнор-листа: список записей с кнопкой удаления + «очистить всё».
    Позволяет «разскрыть» трек, ранее скрытый кнопкой в списке синхронизации."""

    def __init__(self, title: str, entries: set[str], on_remove: Callable[[str], None],
                 on_clear: Callable[[], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._locales = Locales()
        self._on_remove = on_remove
        self._on_clear = on_clear
        self._rows: dict[str, QWidget] = {}

        self.widget.setMinimumWidth(560)
        self.viewLayout.addWidget(SubtitleLabel(title))

        self._scroll = ScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(340)
        self._scroll.setStyleSheet('QScrollArea{border:none;background:transparent;}')
        self._scroll.viewport().setStyleSheet('background:transparent;')
        self._container = QWidget()
        self._container.setStyleSheet('background:transparent;')
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setContentsMargins(0, 0, 6, 0)
        self._vbox.setSpacing(4)
        self._vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        self.viewLayout.addWidget(self._scroll)

        self._empty = BodyLabel(self._locales.get_string('ignore_empty'))
        self._empty.setTextColor(QColor(Config.GRAY_COLOR_600), QColor(Config.GRAY_COLOR_300))
        self._vbox.addWidget(self._empty)

        self._clear_btn = PushButton(self._locales.get_string('clear_all'))
        self._clear_btn.clicked.connect(self._clear)
        self.viewLayout.addWidget(self._clear_btn, 0, Qt.AlignmentFlag.AlignRight)

        for name in sorted(entries):
            self._add_row(name)
        self._refresh_empty()                      # после создания _clear_btn

        self.yesButton.hide()
        self.cancelButton.setText(self._locales.get_string('close'))

    def _add_row(self, name: str) -> None:
        row = SimpleCardWidget()
        row.setFixedHeight(42)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 0, 6, 0)
        label = BodyLabel(name)
        button = TransparentToolButton(FluentIcon.DELETE)
        button.setFixedSize(30, 30)
        button.clicked.connect(lambda _checked=False, n=name: self._remove(n))
        layout.addWidget(label, 1)
        layout.addWidget(button)
        self._vbox.insertWidget(self._vbox.count() - 1, row)   # перед меткой «пусто»
        self._rows[name] = row

    def _remove(self, name: str) -> None:
        self._on_remove(name)
        row = self._rows.pop(name, None)
        if row is not None:
            row.setParent(None)
            row.deleteLater()
        self._refresh_empty()

    def _clear(self) -> None:
        self._on_clear()
        for row in self._rows.values():
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()
        self._refresh_empty()

    def _refresh_empty(self) -> None:
        self._empty.setVisible(not self._rows)
        self._clear_btn.setEnabled(bool(self._rows))


class IgnoreListCard(PushSettingCard):
    """Карточка настроек, открывающая редактор игнор-листа (local или server)."""

    def __init__(self, kind: str, parent: Optional[QWidget] = None) -> None:
        loc = Locales()
        self._kind = kind
        self._db = DataBase()
        title = loc.get_string('local_ignore_title' if kind == 'local' else 'server_ignore_title')
        desc = loc.get_string('local_ignore_description' if kind == 'local' else 'server_ignore_description')
        super().__init__(loc.get_string('manage_ignore_btn'), FluentIcon.HIDE, title, desc, parent)
        self._locales = loc
        self.clicked.connect(self._open)

    def _open(self) -> None:
        if self._kind == 'local':
            entries, on_remove, on_clear, title = (
                self._db.get_local_ignore(), self._db.delete_local_ignore,
                self._db.clear_local_ignore, self._locales.get_string('local_ignore_title'))
        else:
            entries, on_remove, on_clear, title = (
                self._db.get_server_ignore(), self._db.delete_server_ignore,
                self._db.clear_server_ignore, self._locales.get_string('server_ignore_title'))
        IgnoreListDialog(title, entries, on_remove, on_clear, find_mega_parent(self)).exec()


class SettingSection(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        self._l_title = TitleLabel(self)
        self._l_title.setText(title)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._layout.addWidget(self._l_title)
        self._layout.addSpacing(12)


class DownloadSettings(SettingSection):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        loc = Locales()
        super().__init__(loc.get_string('download_params'), parent)

        self._folder = FolderSettingCard(self)

        self._threads = SpinBoxSettingCard(
            spotify_config.download_threads,
            FluentIcon.SPEED_HIGH.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('threads_title'), loc.get_string('threads_desc'), self)

        self._overwrite = CustomSwitchingCard(
            FluentIcon.SAVE_AS.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('overwrite_title'), loc.get_string('overwrite_desc'),
            spotify_config.overwrite_tracks, self)

        self._auto_compare = CustomSwitchingCard(
            FluentIcon.SYNC.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('auto_compare_title'), loc.get_string('auto_compare_desc'),
            spotify_config.auto_compare, self)

        self._headless = CustomSwitchingCard(
            FluentIcon.ROBOT.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('headless_title'), loc.get_string('headless_desc'),
            spotify_config.turnstile_headless, self)

        self._ignore_local = IgnoreListCard('local', self)
        self._ignore_server = IgnoreListCard('server', self)

        for card in (self._folder, self._threads, self._overwrite, self._auto_compare,
                     self._headless, self._ignore_local, self._ignore_server):
            _dim(card)
            self._layout.addWidget(card)


class AccountSettings(SettingSection):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        loc = Locales()
        super().__init__(loc.get_string('account_params'), parent)
        self._clear = ClearAccountCard(self)
        _dim(self._clear)
        self._layout.addWidget(self._clear)


class AppSettings(SettingSection):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        loc = Locales()
        super().__init__(loc.get_string('application'), parent)

        self._theme = CustomComboBoxSettingCard(
            spotify_config.app_theme,
            FluentIcon.PALETTE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('app_theme'), loc.get_string('app_theme_desc'),
            texts=[loc.get_string('dark_theme'), loc.get_string('light_theme'), loc.get_string('auto_theme')],
            parent=self)

        self._language = CustomComboBoxSettingCard(
            spotify_config.app_language,
            FluentIcon.LANGUAGE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('app_language'), loc.get_string('app_language_desc'),
            texts=['Русский', 'English'], parent=self)

        self._auto_update = CustomSwitchingCard(
            FluentIcon.UPDATE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            loc.get_string('auto_update_title'), loc.get_string('auto_update_desc'),
            spotify_config.auto_update, self)

        self._about = AboutUpdateCard(self)

        for card in (self._theme, self._language, self._auto_update, self._about):
            _dim(card)
            self._layout.addWidget(card)
