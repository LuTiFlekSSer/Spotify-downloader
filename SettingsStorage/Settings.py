__all__ = [
    'Settings'
]

import sqlite3 as sql
from SettingsStorage import Errors
from os import path, getenv, mkdir
from multiprocessing import cpu_count


class Settings:
    def __init__(self):
        settings_exists = False

        self._path = f'{getenv("APPDATA")}\\Spotify downloader'

        if not path.exists(self._path):
            mkdir(self._path)

        if path.isfile(self._path + '\\settings.db'):
            settings_exists = True

        self._data = sql.connect(self._path + '\\settings.db')

        cur = self._data.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS server_ignore ('name' TEXT PRIMARY KEY);")
        cur.execute("CREATE TABLE IF NOT EXISTS local_ignore ('name' TEXT PRIMARY KEY);")
        cur.execute("CREATE TABLE IF NOT EXISTS app_settings ('name' TEXT PRIMARY KEY, 'value' TEXT);")

        if not settings_exists:
            self._set_base_settings()

        self._data.commit()

    def _set_base_settings(self):
        cur = self._data.cursor()

        cur.execute(f"INSERT INTO app_settings VALUES ('threads', '{cpu_count()}')")
        cur.execute(f"INSERT INTO app_settings VALUES ('path_for_sync', '')")
        cur.execute(f"INSERT INTO app_settings VALUES ('auto_comp', 'True')")
        cur.execute(f"INSERT INTO app_settings VALUES ('client_id', '')")
        cur.execute(f"INSERT INTO app_settings VALUES ('client_secret', '')")
        cur.execute(f"INSERT INTO app_settings VALUES ('redirect_uri', '')")
        cur.execute(f"INSERT INTO app_settings VALUES ('code', '')")

    def get_setting(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        cur.execute(f"SELECT value FROM app_settings WHERE name = '{name}'")
        value = cur.fetchall()

        if len(value) == 0:
            raise Errors.NotFoundError

        return value[0][0]

    def change_setting(self, name, value):
        if not (isinstance(name, str) and isinstance(value, str)):
            raise TypeError

        cur = self._data.cursor()

        cur.execute(f"UPDATE app_settings SET 'value' = '{value}' WHERE name = '{name}'")

        self._data.commit()

    def add_track_to_server_ignore(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        try:
            cur.execute(f"INSERT INTO server_ignore VALUES ('{name}')")
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

        self._data.commit()

    def get_all_server_ignore_tracks(self):
        cur = self._data.cursor()

        cur.execute("SELECT * FROM server_ignore")

        result = cur.fetchall()
        server_ignore_list = set()

        for track in result:
            server_ignore_list.add(track[0])

        return server_ignore_list

    def add_track_to_local_ignore(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        try:
            cur.execute(f"INSERT INTO local_ignore VALUES ('{name}')")
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

        self._data.commit()

    def get_all_local_ignore_tracks(self):
        cur = self._data.cursor()

        cur.execute("SELECT * FROM local_ignore")

        result = cur.fetchall()
        local_ignore_list = set()

        for track in result:
            local_ignore_list.add(track[0])

        return local_ignore_list
