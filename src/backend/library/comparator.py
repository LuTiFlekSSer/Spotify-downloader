import os
import time

from mutagen import File as MutagenFile

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track
from src.backend.library.formats import AUDIO_EXTENSIONS


class Comparator:
    """Сравнивает локальные треки с любимыми Spotify (логика старого Comparator).

    local_missing  — есть в Spotify, нет локально (нужно скачать), с полными данными.
    server_missing — есть локально, нет в любимых Spotify (минус server_ignore).
    Самолечение: трек переименован в Spotify (id совпал, имя — нет) -> переименовать
    файл на диске, перетегировать и поправить library."""

    def __init__(self, local_tracks: set[tuple[str, str]], spotify_tracks: dict[str, Track],
                 directory: str, db: DataBase | None = None) -> None:
        self._local = set(local_tracks)
        self._spotify = spotify_tracks            # name -> Track (name = build_filename)
        self._directory = directory
        self._db = db or DataBase()

    def compute(self) -> tuple[list[str], list[Track]]:
        spotify_names = set(self._spotify.keys())
        spotify_by_id = {t.id: name for name, t in self._spotify.items()}

        missing = set(spotify_names)              # ещё не сопоставленные со Spotify

        for name, track_id in list(self._local):
            if name in spotify_names:
                missing.discard(name)
                correct = self._spotify[name].id
                if track_id != correct:
                    self._db.set_library_track(name, correct)
            elif track_id != 'None' and track_id in spotify_by_id:
                new_name = spotify_by_id[track_id]
                if self._rename(name, new_name, self._spotify[new_name]):
                    self._local.discard((name, track_id))
                    self._local.add((new_name, track_id))
                    missing.discard(new_name)

        local_names = {name for name, _ in self._local}
        server_ignore = self._db.get_server_ignore()
        server_missing = sorted(local_names - spotify_names - server_ignore)
        local_missing = [self._spotify[name] for name in missing]

        return server_missing, local_missing

    def _find_file(self, name: str) -> tuple[str, str] | None:
        """Возвращает (путь, расширение) первого существующего файла трека по имени."""
        for ext in AUDIO_EXTENSIONS:
            path = os.path.join(self._directory, name + ext)
            if os.path.exists(path):
                return path, ext
        return None

    def _rename(self, old_name: str, new_name: str, track: Track) -> bool:
        found = self._find_file(old_name)
        if found is None:
            return False                           # файла нет ни в одном формате
        old_path, ext = found
        new_path = os.path.join(self._directory, new_name + ext)   # сохраняем формат

        ok = False
        for _ in range(3):
            try:
                os.rename(old_path, new_path)
                ok = True
                break
            except OSError:
                time.sleep(0.1)
        if not ok:
            return False

        self._retag(new_path, track)               # апгрейд метаданных (любой формат)

        self._db.delete_library_track(old_name)
        self._db.set_library_track(new_name, track.id)
        return True

    @staticmethod
    def _retag(path: str, track: Track) -> None:
        """Обновляет title/artist у файла любого формата через mutagen (тег не критичен —
        файл уже переименован, поэтому ошибки глотаем)."""
        try:
            audio = MutagenFile(path, easy=True)
            if audio is None:
                return
            audio['title'] = [track.title]
            audio['artist'] = ['/'.join(track.artists)]
            audio.save()
        except Exception:
            pass
