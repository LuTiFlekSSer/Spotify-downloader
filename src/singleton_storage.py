from src.backend.db.data_base import DataBase
from src.global_flags import GlobalFlags
from src.locales.locales import Locales


class SingletonStorage:
    """Eager-init всех синглтонов на старте: держит strong-ref, чтобы
    WeakValueDictionary в Singleton не собрал их GC. По мере роста сюда
    добавляются SpotiSession, DownloaderPool и т.д."""

    def __init__(self):
        DataBase()
        GlobalFlags()
        Locales()
