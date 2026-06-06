import os
from typing import Callable, Optional

from src.backend.db.data_base import DataBase


class LocalScanner:
    """Сканирует папку на .mp3 и сверяет с library (имя файла -> spotify id).

    Новые файлы заносятся в library с id 'None'; исчезнувшие удаляются.
    Возвращает set (name, track_id). 'None' — строковый sentinel неизвестного id
    (контракт сохранён со старым приложением)."""

    def __init__(self, directory: str, db: DataBase | None = None) -> None:
        self._directory = directory
        self._db = db or DataBase()

    def scan(self, progress: Optional[Callable[[int, int], None]] = None) -> set[tuple[str, str]]:
        files = [f for f in os.listdir(self._directory) if f.lower().endswith('.mp3')]
        known = self._db.get_library()        # name -> id (копия)
        remaining = dict(known)
        local: set[tuple[str, str]] = set()
        total = len(files)

        for i, filename in enumerate(files):
            name = filename[:-4]               # без .mp3
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
