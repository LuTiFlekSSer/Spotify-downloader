__all__ = [
    'Settings'
]

import sqlite3 as sql
from SettingsStorage import Errors
from os import path, getenv, mkdir
from multiprocessing import cpu_count
import Version


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
        cur.execute("CREATE TABLE IF NOT EXISTS tracks_id ('name' TEXT PRIMARY KEY, 'track_id' TEXT);")

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
        cur.execute(f"INSERT INTO app_settings VALUES ('version', '{Version.__version__}')")
        cur.execute(f"INSERT INTO app_settings VALUES ('auto_update', 'True')")
        cur.execute(f"INSERT INTO app_settings VALUES ('overwrite_tracks', 'False')")
        cur.execute(f"INSERT INTO app_settings VALUES ('language', 'None')")
        cur.execute(f"INSERT INTO app_settings VALUES ('window_size', '640*400')")
        cur.execute(f"INSERT INTO app_settings VALUES ('window_mode', 'normal')")

    def get_setting(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        cur.execute(f"SELECT value FROM app_settings WHERE name = ?", (name,))
        value = cur.fetchall()

        if len(value) == 0:
            raise Errors.NotFoundError

        return value[0][0]

    def change_setting(self, name, value):
        if not (isinstance(name, str) and isinstance(value, str)):
            raise TypeError

        cur = self._data.cursor()

        cur.execute(f"UPDATE app_settings SET value = ? WHERE name = ?", (value, name))

        self._data.commit()

    def get_string(self, string_name):
        if not isinstance(string_name, str):
            raise TypeError

        cur = self._data.cursor()

        language = self.get_setting('language')

        cur.execute(f"SELECT {language} FROM locales WHERE string_name = ?", (string_name,))
        value = cur.fetchall()

        if len(value) == 0:
            raise Errors.NotFoundError

        return value[0][0]

    def create_setting(self, name, value):
        if not (isinstance(name, str) and isinstance(value, str)):
            raise TypeError

        cur = self._data.cursor()

        try:
            cur.execute(f"INSERT INTO app_settings VALUES (?, ?)", (name, value))
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

        self._data.commit()

    def add_track_to_server_ignore(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        try:
            cur.execute(f"INSERT INTO server_ignore VALUES (?)", (name,))
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

    def delete_track_from_server_ignore(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        cur.execute(f"SELECT * FROM server_ignore WHERE name = ?", (name,))
        result = cur.fetchall()

        if len(result) != 0:
            cur.execute(f"DELETE FROM server_ignore WHERE name = ?", (name,))
        else:
            raise Errors.NotFoundError

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
            cur.execute(f"INSERT INTO local_ignore VALUES (?)", (name,))
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

    def delete_track_from_local_ignore(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        cur.execute(f"SELECT * FROM local_ignore WHERE name = ?", (name,))
        result = cur.fetchall()

        if len(result) != 0:
            cur.execute(f"DELETE FROM local_ignore WHERE name = ?", (name,))
        else:
            raise Errors.NotFoundError

    def get_all_local_ignore_tracks(self):
        cur = self._data.cursor()

        cur.execute("SELECT * FROM local_ignore")

        result = cur.fetchall()
        local_ignore_list = set()

        for track in result:
            local_ignore_list.add(track[0])

        return local_ignore_list

    def get_path(self):
        return self._path

    def get_local_tracks_db(self):
        cur = self._data.cursor()

        cur.execute("SELECT * FROM tracks_id")

        result = cur.fetchall()

        return dict(result)

    def change_local_track_id(self, name, new_id):
        cur = self._data.cursor()

        cur.execute(f"UPDATE tracks_id SET track_id = ? WHERE name = ?", (new_id, name))

    def add_track_to_local_tracks(self, name, track_id):
        cur = self._data.cursor()

        try:
            cur.execute(f"INSERT INTO tracks_id VALUES (?,?)", (name, track_id))

        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

    def save(self):
        self._data.commit()

    def delete_local_track(self, name):
        cur = self._data.cursor()

        cur.execute(f"SELECT * FROM tracks_id WHERE name = ?", (name,))
        result = cur.fetchall()

        if len(result) != 0:
            cur.execute(f"DELETE FROM tracks_id WHERE name = ?", (name,))
        else:
            raise Errors.NotFoundError
