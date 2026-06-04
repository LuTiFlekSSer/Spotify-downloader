import sys
import time

from PySide6.QtCore import QSize, QEventLoop, QTimer, Qt, Signal, QEvent
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (SplashScreen, FluentIcon, MSFluentWindow, NavigationItemPosition,
                            setTheme, Theme, setThemeColor, SystemThemeListener, InfoBar, InfoBarPosition)

from src.backend.db.data_base import DataBase
from src.frontend.home_window.home_window import HomeWindow
from src.frontend.placeholder import PlaceholderPage
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.config import Config
from src.version import __version__

try:
    from qframelesswindow.utils import getSystemAccentColor
except Exception:
    getSystemAccentColor = None


class MainWindow(MSFluentWindow):
    sig_external_command: Signal = Signal(str, str)
    sig_to_front: Signal = Signal()

    def __init__(self, app: QApplication):
        super().__init__()

        self.ULTRA_MEGA_PARENT: str = 'parent'

        self._locales: Locales = Locales()
        self._db: DataBase = DataBase()
        self._global_flags: GlobalFlags = GlobalFlags()

        setTheme(getattr(Theme, self._db.get_setting('theme')))
        if getSystemAccentColor is not None:
            try:
                setThemeColor(getSystemAccentColor(), save=False)
            except Exception:
                pass
        self._theme_listener = SystemThemeListener(self)
        self._theme_listener.systemThemeChanged.connect(
            lambda: setTheme(getattr(Theme, self._db.get_setting('theme')))
        )

        self.resize(*map(int, self._db.get_setting('window_size').split()))
        self.setMinimumWidth(840)
        self.setMinimumHeight(480)

        self.setWindowTitle(f'{Config.APP_NAME} v{__version__}')
        self.setWindowIcon(QIcon(Config.WINDOW_ICON))
        try:
            self.setMicaEffectEnabled(True)   # полупрозрачный фон Mica (Windows 11)
        except Exception:
            pass
        self._center()

        self._splashscreen: SplashScreen = SplashScreen(self.windowIcon(), self)
        self._splashscreen.setIconSize(QSize(120, 120))
        self._splashscreen.titleBar.hide()
        self.show()

        self._init_screen()

        self._splashscreen.finish()
        self._theme_listener.start()

        if self._db.get_setting('window_mode') == 'maximized':
            self.showMaximized()

    def _init_screen(self):
        init_start = time.time()

        self._home_window = HomeWindow(self._locales.get_string('home'), parent=self)
        self.addSubInterface(self._home_window, FluentIcon.HOME, self._locales.get_string('home'))

        self._tracks_window = PlaceholderPage(
            'tracks', self._locales.get_string('tracks'),
            self._locales.get_string('tracks_placeholder'), parent=self)
        self.addSubInterface(self._tracks_window, FluentIcon.MUSIC, self._locales.get_string('tracks'))

        self._settings_window = PlaceholderPage(
            'settings', self._locales.get_string('settings'),
            self._locales.get_string('settings_placeholder'), parent=self)
        self.addSubInterface(self._settings_window, FluentIcon.SETTING,
                             self._locales.get_string('settings'),
                             position=NavigationItemPosition.BOTTOM)

        self.sig_to_front.connect(self._on_sig_to_front)

        if (init_time := (time.time() - init_start)) < Config.SPLASH_SCREEN_TIME:
            loop = QEventLoop(self)
            QTimer.singleShot(int((Config.SPLASH_SCREEN_TIME - init_time) * 1000), loop.quit)
            loop.exec()

    def _on_sig_to_front(self):
        self.activateWindow()
        self.raise_()

    def _center(self):
        screen = QGuiApplication.primaryScreen()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.availableGeometry().center())
        self.move(window_geometry.topLeft())

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange and self.isMaximized():
            self._db.set_setting('window_mode', 'maximized')

        super().changeEvent(event)

    def closeEvent(self, event):
        if self._global_flags.is_running.is_set():
            InfoBar.error(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('close_error_message'),
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self,
            )
            event.ignore()
            return

        if self.isMaximized():
            self._db.set_setting('window_mode', 'maximized')
        else:
            self._db.set_setting('window_size', f'{self.width()} {self.height()}')
            self._db.set_setting('window_mode', 'normal')

        self._theme_listener.terminate()
        self._theme_listener.deleteLater()
        self._global_flags.stop_event.set()

        event.accept()


def create_ui() -> tuple[QApplication, MainWindow]:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    window = MainWindow(app)
    window.show()

    return app, window
