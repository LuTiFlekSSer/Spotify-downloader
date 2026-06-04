"""Контракт имён файлов — ДОЛЖЕН совпадать побайтно со старым приложением,
иначе уже скачанные mp3 перестанут матчиться при синхронизации.

Источник: старый SpotifyTracks.SpTracks.dict_for_replace + TrackDownloader.create_download_query.
Имя файла = "<title> - <artist1><sep><artist2>" с заменой запрещённых символов на Unicode-двойники.
Кодпойнты заданы \\u-эскейпами намеренно — чтобы исключить дрейф глифов.
"""

# разделитель артистов в имени файла (U+29F8 BIG SOLIDUS)
ARTIST_SEPARATOR = '⧸'

# запрещённые в Windows символы -> визуально похожие Unicode (ВЕРБАТИМ из старого кода)
DICT_FOR_REPLACE: dict[str, str] = {
    '/': '⧸',
    '\\': '⧹',
    ':': 'ꓽ',
    '"': '″',
    '*': '⁎',
    '?': 'ʔ',
    '<': 'ᐸ',
    '>': 'ᐳ',
    '|': '∣',
}

_TRANS = str.maketrans(DICT_FOR_REPLACE)


def build_filename(title: str, artists: list[str]) -> str:
    """Имя файла без расширения: '<title> - <a1><sep><a2>' с заменой символов.
    artists — список имён артистов (для liked — из spotipy как есть)."""
    joined = ARTIST_SEPARATOR.join(a.strip() for a in artists)
    return f'{title} - {joined}'.translate(_TRANS)
