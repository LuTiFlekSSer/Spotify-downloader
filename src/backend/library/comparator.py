import os
import time

import eyed3

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track

eyed3.log.setLevel('ERROR')


class Comparator:
    """Сравнивает локальные треки с любимыми Spotify (логика старого Comparator).

    local_missing  — есть в Spotify, нет локально (нужно скачать), с полными данными.
    server_missing — есть локально, нет в любимых Spotify (минус server_ignore).
    Самолечение: трек переименован в Spotify (id совпал, имя — нет) -> переименовать
    файл на диске, перетегировать и поправить library."""

    def __init__(self, local_tracks: set[tuple[str, str]], spotify_tracks: dict[str, Track],
                 directory: str, db: DataBase | None = None):
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

    def _rename(self, old_name: str, new_name: str, track: Track) -> bool:
        old_path = os.path.join(self._directory, f'{old_name}.mp3')
        new_path = os.path.join(self._directory, f'{new_name}.mp3')

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

        try:
            audio = eyed3.load(new_path)
            if audio is not None:
                if audio.tag is None:
                    audio.initTag()
                audio.tag.title = track.title
                audio.tag.artist = '/'.join(track.artists)
                audio.tag.save()
        except Exception:
            pass                                   # тег не критичен — файл уже переименован

        self._db.delete_library_track(old_name)
        self._db.set_library_track(new_name, track.id)
        return True
