from src.backend.db.data_base import DataBase
from src.backend.db.migration import migrate_old_settings_db
from src.backend.download.pool import DownloaderPool
from src.backend.spotidl.session import SpotiSession
from src.backend.spotify.session import SpotifySession
from src.global_flags import GlobalFlags
from src.locales.locales import Locales


class SingletonStorage:
    """Eager-init всех синглтонов на старте: держит strong-ref, чтобы
    WeakValueDictionary в Singleton не собрал их GC."""

    def __init__(self) -> None:
        DataBase()
        migrate_old_settings_db()   # импорт старого settings.db (до Locales: язык может прийти оттуда)
        GlobalFlags()
        Locales()
        SpotifySession()            # Spotify OAuth (любимые треки)
        SpotiSession()              # сессия spotidownloader (ключ загрузки)
        DownloaderPool()            # движок загрузки
