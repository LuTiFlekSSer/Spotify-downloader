from dataclasses import dataclass
from enum import Enum, auto


class TrackStatus(Enum):
    """Рантайм-статус трека в таблице/очереди загрузки.
    Соответствует старому TrackDownloader.Status + UI-состояниям."""
    MISSING = auto()          # есть в Spotify, нет локально (до загрузки)
    QUEUED = auto()           # в очереди
    DOWNLOADING = auto()      # скачивается
    DOWNLOADED = auto()       # успешно (старый Status.OK)
    SKIPPED = auto()          # уже на диске, пропущен
    DOWNLOAD_ERROR = auto()   # старый API_ERR / GET_ERR
    NOT_FOUND = auto()        # старый NF_ERR
    JPG_ERROR = auto()        # старый JPG_ERR (обложка)
    TAG_ERROR = auto()        # старый TAG_ERR (метаданные)
    CANCELLED = auto()        # отменён
    LINK_ERROR = auto()       # некорректная ссылка (старый LINK_ERR)


# TrackStatus -> ключ строки в locales.json (используется UI в Фазе 4)
TRACK_STATUS_LOCALE: dict[TrackStatus, str] = {
    TrackStatus.MISSING: 'state_missing',
    TrackStatus.QUEUED: 'state_missing',
    TrackStatus.DOWNLOADING: 'downloading',
    TrackStatus.DOWNLOADED: 'downloaded',
    TrackStatus.SKIPPED: 'downloaded',
    TrackStatus.DOWNLOAD_ERROR: 'download_error',
    TrackStatus.NOT_FOUND: 'nf_error',
    TrackStatus.JPG_ERROR: 'jpg_error',
    TrackStatus.TAG_ERROR: 'tag_error',
    TrackStatus.CANCELLED: 'cancelled',
    TrackStatus.LINK_ERROR: 'multiple_link_error',
}


@dataclass
class Track:
    """Каноническая модель трека через все слои (fetch -> download -> UI).
    Поля совпадают с формой нового API spotidownloader (/tracks, /download.metadata)
    и со старым create_download_query."""
    id: str
    title: str
    artists: str = ''          # как отдаёт API — через запятую: 'Artist1, Artist2'
    album: str = ''
    release_date: str = ''     # год (YYYY)
    cover: str = ''            # URL обложки
    status: TrackStatus = TrackStatus.MISSING

    @classmethod
    def from_api(cls, data: dict) -> 'Track':
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            artists=data.get('artists', ''),
            album=data.get('album', '') or '',
            release_date=(data.get('releaseDate') or '')[:4],
            cover=data.get('cover', '') or '',
        )
