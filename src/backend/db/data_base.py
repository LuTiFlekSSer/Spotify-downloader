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
    'client_id',
    'client_secret',
    'redirect_uri',
    'migrated_from_old',
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
    'client_id': '',
    'client_secret': '',
    'redirect_uri': '',
    'migrated_from_old': 'False',
}


class DataBase(metaclass=Singleton):
    """Единое потокобезопасное хранилище: один sqlite-коннект (check_same_thread=False)
    под одним Lock.

    Таблицы:
      settings(name PK, value)        — конфиг ключ/значение (все значения строки)
      library(name PK, track_id)      — карта «уже скачано»: имя файла -> spotify id (бывш. tracks_id)
      local_ignore(name PK)           — игнор при получении любимых
      server_ignore(name PK)          — игнор при поиске отсутствующих на сервере
    """

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

            curr.execute('''CREATE TABLE IF NOT EXISTS settings (
                                'name' TEXT PRIMARY KEY NOT NULL,
                                'value' TEXT NOT NULL)''')
            curr.execute('''CREATE TABLE IF NOT EXISTS library (
                                'name' TEXT PRIMARY KEY NOT NULL,
                                'track_id' TEXT NOT NULL)''')
            curr.execute('''CREATE TABLE IF NOT EXISTS local_ignore (
                                'name' TEXT PRIMARY KEY NOT NULL)''')
            curr.execute('''CREATE TABLE IF NOT EXISTS server_ignore (
                                'name' TEXT PRIMARY KEY NOT NULL)''')

            for name, value in _DEFAULTS.items():
                curr.execute('''INSERT INTO settings
                                SELECT ?, ?
                                WHERE ? NOT IN (SELECT name FROM settings)''',
                             (name, value, name))

            self._connection.commit()

    # ---------- settings ----------
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
            curr.execute('''INSERT INTO settings (name, value) VALUES (?, ?)
                            ON CONFLICT(name) DO UPDATE SET value = excluded.value''',
                         (setting, value))
            self._connection.commit()

    # ---------- library (карта скачанного) ----------
    def get_library(self) -> dict[str, str]:
        with self._lock:
            curr = self._connection.cursor()
            curr.execute('SELECT name, track_id FROM library')
            return dict(curr.fetchall())

    def set_library_track(self, name: str, track_id: str):
        """Upsert: добавить/обновить запись имя -> spotify id."""
        with self._lock:
            curr = self._connection.cursor()
            curr.execute('''INSERT INTO library (name, track_id) VALUES (?, ?)
                            ON CONFLICT(name) DO UPDATE SET track_id = excluded.track_id''',
                         (name, track_id))
            self._connection.commit()

    def delete_library_track(self, name: str):
        with self._lock:
            curr = self._connection.cursor()
            curr.execute('DELETE FROM library WHERE name = ?', (name,))
            self._connection.commit()

    # ---------- ignore lists ----------
    def get_local_ignore(self) -> set[str]:
        return self._get_ignore('local_ignore')

    def add_local_ignore(self, name: str):
        self._add_ignore('local_ignore', name)

    def delete_local_ignore(self, name: str):
        self._delete_ignore('local_ignore', name)

    def get_server_ignore(self) -> set[str]:
        return self._get_ignore('server_ignore')

    def add_server_ignore(self, name: str):
        self._add_ignore('server_ignore', name)

    def delete_server_ignore(self, name: str):
        self._delete_ignore('server_ignore', name)

    def _get_ignore(self, table: str) -> set[str]:
        with self._lock:
            curr = self._connection.cursor()
            curr.execute(f'SELECT name FROM {table}')
            return {row[0] for row in curr.fetchall()}

    def _add_ignore(self, table: str, name: str):
        with self._lock:
            curr = self._connection.cursor()
            curr.execute(f'INSERT OR IGNORE INTO {table} (name) VALUES (?)', (name,))
            self._connection.commit()

    def _delete_ignore(self, table: str, name: str):
        with self._lock:
            curr = self._connection.cursor()
            curr.execute(f'DELETE FROM {table} WHERE name = ?', (name,))
            self._connection.commit()
