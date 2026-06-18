import os
from typing import Callable, Optional

from src.backend.db.data_base import DataBase
from src.backend.library.formats import AUDIO_EXTENSIONS


class LocalScanner:
    """Сканирует папку на поддерживаемые аудиоформаты (mp3/flac/m4a/ogg/opus) и сверяет
    с library (имя файла без расширения -> spotify id).

    Новые файлы заносятся в library с id 'None'; исчезнувшие удаляются.
    Возвращает set (name, track_id). 'None' — строковый sentinel неизвестного id
    (контракт сохранён со старым приложением). Сопоставление — по имени БЕЗ расширения,
    поэтому один трек считается одним независимо от формата."""

    def __init__(self, directory: str, db: DataBase | None = None) -> None:
        self._directory = directory
        self._db = db or DataBase()

    def scan(self, progress: Optional[Callable[[int, int], None]] = None) -> set[tuple[str, str]]:
        # один файл на имя без расширения: если трек лежит сразу в нескольких форматах,
        # берём первый по сортировке (порядок детерминирован) — трек считается одним.
        by_name: dict[str, str] = {}
        for filename in sorted(os.listdir(self._directory)):
            if filename.lower().endswith(AUDIO_EXTENSIONS):
                name = os.path.splitext(filename)[0]
                by_name.setdefault(name, filename)

        known = self._db.get_library()        # name -> id (копия)
        remaining = dict(known)
        local: set[tuple[str, str]] = set()
        total = len(by_name)

        for i, name in enumerate(by_name):
            if name in remaining:
                track_id = remaining.pop(name)
            else:
                track_id = 'None'
                self._db.set_library_track(name, 'None')
            local.add((name, track_id))
            if progress:
                progress(i + 1, total)

        for vanished in remaining:             # были в library, но файла нет
            self._db.delete_library_track(vanished)

        return local
