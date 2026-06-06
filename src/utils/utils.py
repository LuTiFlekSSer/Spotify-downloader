import os
import re
import sys

from PySide6.QtWidgets import QWidget
from qfluentwidgets import MSFluentWindow


def resource_path(relative_path: str) -> str:
    """Путь к бандл-ресурсу: работает и из исходников (cwd закреплён в main.py),
    и из onefile-сборки (sys._MEIPASS)."""
    base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base, relative_path)


def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def get_executable_path() -> str:
    """Путь к текущему исполняемому файлу: .exe в сборке, иначе main.py."""
    if is_frozen():
        return sys.executable
    import __main__
    return getattr(__main__, '__file__', None) or os.path.abspath('main.py')


def compare_versions(current: str, new: str) -> bool:
    """True, если `new` строго новее `current`. Сравнение по числовым сегментам
    (исправляет старый баг лексикографического сравнения '10' < '9')."""

    def parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in re.findall(r'\d+', v))

    return parse(new) > parse(current)


def get_normalized_size(locales, size: float) -> str:
    for unit in (locales.get_string('B'),
                 locales.get_string('KB'),
                 locales.get_string('MB'),
                 locales.get_string('GB'),
                 locales.get_string('TB')):
        if size < 1024:
            return f'{size:.2f} {unit}'
        size /= 1024

    return f'{size:.2f} {locales.get_string("PB")}'


def setup_logging():
    """Логирование в файл — у frozen-сборки нет консоли, поэтому ошибки иначе теряются.
    Пишет в %APPDATA%/Spotify Downloader/debug.log (с ротацией). Возвращает путь к логу."""
    import logging
    from logging.handlers import RotatingFileHandler
    from src.utils.config import Config

    try:
        os.makedirs(Config.APP_DATA_DIR, exist_ok=True)
        path = os.path.join(Config.APP_DATA_DIR, 'debug.log')
        handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=2, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
            root.addHandler(handler)
        return path
    except Exception:
        return None


def find_mega_parent(widget: QWidget) -> QWidget:
    """Идёт вверх по .parent() до MSFluentWindow с маркером ULTRA_MEGA_PARENT."""
    tmp_widget = widget

    while True:
        if isinstance(tmp_widget, MSFluentWindow) and hasattr(tmp_widget, 'ULTRA_MEGA_PARENT'):
            return tmp_widget
        if tmp_widget is None:
            return widget

        tmp_widget = tmp_widget.parent()
