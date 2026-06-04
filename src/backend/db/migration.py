import os
import sqlite3

from src.backend.db.data_base import DataBase
from src.utils.config import Config

# старый ключ app_settings -> новый ключ settings
_SETTING_MAP: dict[str, str] = {
    'threads': 'threads',
    'path_for_sync': 'download_dir',
    'auto_comp': 'auto_compare',
    'overwrite_tracks': 'overwrite_tracks',
    'auto_update': 'auto_update',
    'language': 'language',
    'window_size': 'window_size',
    'window_mode': 'window_mode',
    'client_id': 'client_id',
    'client_secret': 'client_secret',
    'redirect_uri': 'redirect_uri',
}


def migrate_old_settings_db():
    """Однократный импорт старой БД CustomTkinter-версии (%APPDATA%/Spotify downloader/settings.db).
    Переносит настройки, карту скачанного (tracks_id -> library) и оба игнор-листа.
    Старый OAuth 'code' НЕ переносим (переходим на refresh-token через spotipy .cache,
    который лежит по тому же пути и подхватится автоматически)."""

    db = DataBase()

    if db.get_setting('migrated_from_old') == 'True':
        return

    old_path = Config.OLD_SETTINGS_DB
    if not os.path.exists(old_path):
        db.set_setting('migrated_from_old', 'True')
        return

    try:
        conn = sqlite3.connect(f'file:{old_path}?mode=ro', uri=True)
        cur = conn.cursor()

        tables = {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        if 'app_settings' in tables:
            old_settings = dict(cur.execute('SELECT name, value FROM app_settings').fetchall())
            for old_key, new_key in _SETTING_MAP.items():
                if old_key not in old_settings:
                    continue
                value = old_settings[old_key]
                if new_key == 'window_size':
                    value = value.replace('*', ' ')   # старый формат 'W*H' -> 'W H'
                db.set_setting(new_key, value)

        if 'tracks_id' in tables:
            for name, track_id in cur.execute('SELECT name, track_id FROM tracks_id').fetchall():
                db.set_library_track(name, track_id)

        if 'local_ignore' in tables:
            for (name,) in cur.execute('SELECT name FROM local_ignore').fetchall():
                db.add_local_ignore(name)

        if 'server_ignore' in tables:
            for (name,) in cur.execute('SELECT name FROM server_ignore').fetchall():
                db.add_server_ignore(name)

        conn.close()
    except Exception:
        # миграция не должна валить старт — просто помечаем выполненной
        pass

    db.set_setting('migrated_from_old', 'True')
