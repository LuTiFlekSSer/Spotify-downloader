__all__ = [
    'Settings'
]

import sqlite3 as sql
from SettingsStorage import Errors


class Settings:
    def __init__(self):
        self._data = sql.connect('settings.db')

        cur = self._data.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS 'server_ignore' ('name' TEXT PRIMARY KEY);")
        cur.execute("CREATE TABLE IF NOT EXISTS 'local_ignore' ('name' TEXT PRIMARY KEY);")

        self._data.commit()

    def add_track_to_server_ignore(self, name):
        if not isinstance(name, str):
            raise TypeError

        cur = self._data.cursor()

        try:
            cur.execute(f"INSERT INTO 'server_ignore' VALUES ('{name}')")
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

        self._data.commit()

    def get_all_server_ignore_tracks(self):
        cur = self._data.cursor()

        cur.execute("SELECT * FROM 'server_ignore'")

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
            cur.execute(f"INSERT INTO 'local_ignore' VALUES ('{name}')")
        except sql.IntegrityError:
            raise Errors.AlreadyExistsError

        self._data.commit()

    def get_all_local_ignore_tracks(self):
        cur = self._data.cursor()

        cur.execute("SELECT * FROM 'local_ignore'")

        result = cur.fetchall()
        local_ignore_list = set()

        for track in result:
            local_ignore_list.add(track[0])

        return local_ignore_list
