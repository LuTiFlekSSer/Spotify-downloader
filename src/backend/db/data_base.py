import os
import sqlite3
from os import cpu_count
from threading import Lock
from typing import Literal

from src.utils.config import Config
from src.utils.singleton import Singleton

TSettingName = Literal[
    'language',
    'theme',
    'window_size',
    'window_mode',
    'threads',
    'download_dir',
    'overwrite_tracks',
    'auto_compare',
    'auto_update',
    'turnstile_headless',
]

_DEFAULTS: dict[str, str] = {
    'language': 'None',
    'theme': 'DARK',
    'window_size': '1000 600',
    'window_mode': 'normal',
    'threads': str(cpu_count() or 4),
    'download_dir': '',
    'overwrite_tracks': 'False',
    'auto_compare': 'True',
    'auto_update': 'True',
    'turnstile_headless': 'True',
}


class DataBase(metaclass=Singleton):
    """Единое потокобезопасное хранилище: один sqlite-коннект (check_same_thread=False)
    под одним Lock. Пока только таблица settings; доменные таблицы (tracks/history) и
    ignore-листы добавляются в Фазе 1/3."""

    def __init__(self):
        self._lock: Lock = Lock()

        os.makedirs(Config.DB_PATH, exist_ok=True)
        self._connection = sqlite3.connect(
            os.path.join(Config.DB_PATH, Config.DB_FILENAME),
            check_same_thread=False,
        )

        self._create_db()

    def _create_db(self):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    'name' TEXT PRIMARY KEY NOT NULL,
                    'value' TEXT NOT NULL
                )
            ''')

            for name, value in _DEFAULTS.items():
                curr.execute(
                    '''INSERT INTO settings
                       SELECT ?, ?
                       WHERE ? NOT IN (SELECT name FROM settings)''',
                    (name, value, name),
                )

            self._connection.commit()

    def get_setting(self, setting: TSettingName) -> str:
        with self._lock:
            curr = self._connection.cursor()
            curr.execute('SELECT value FROM settings WHERE name = ?', (setting,))
            row = curr.fetchone()

            if row is None:
                raise ValueError(f'unknown setting: {setting}')

            return row[0]

    def set_setting(self, setting: TSettingName, value: str):
        with self._lock:
            curr = self._connection.cursor()
            curr.execute(
                '''INSERT INTO settings (name, value) VALUES (?, ?)
                   ON CONFLICT(name) DO UPDATE SET value = excluded.value''',
                (setting, value),
            )
            self._connection.commit()
