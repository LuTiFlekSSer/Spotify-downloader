from typing import Any, Callable, Optional

import requests

from src.backend.spotidl import constants, errors
from src.backend.spotidl.session import SpotiSession


class ApiClient:
    """Клиент spotidownloader API. Каждый запрос подставляет актуальный
    Bearer из SpotiSession; на 401/403 делает один force_refresh и повтор."""

    _MAX_TRACKS_PAGES = 200   # предохранитель от бесконечной пагинации

    def __init__(self, session: SpotiSession) -> None:
        self._session = session
        self._http = requests.Session()

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(2):
            token = self._session.get_token()
            response = self._http.post(url, json=payload,
                                       headers=constants.api_headers(token), timeout=30)

            if response.status_code in (401, 403) and attempt == 0:
                self._session.force_refresh(stale_token=token)   # single-flight: см. SpotiSession
                continue

            try:
                response.raise_for_status()
            except requests.RequestException as e:
                raise errors.ApiError(str(e))

            return response.json()

        raise errors.ApiError(f'authorization failed for {url}')

    def metadata(self, type_: str, id_: str) -> dict[str, Any]:
        return self._post(constants.METADATA_URL, {'type': type_, 'id': id_})

    def tracks_page(self, type_: str, id_: str, offset: int) -> dict[str, Any]:
        return self._post(constants.TRACKS_URL, {'type': type_, 'id': id_, 'offset': offset})

    def download_link(self, track_id: str) -> dict[str, Any]:
        return self._post(constants.DOWNLOAD_URL, {'id': track_id})

    def fetch_bytes(self, url: str, timeout: float = 180) -> bytes:
        response = self._http.get(url, timeout=timeout)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            raise errors.ApiError(str(e))
        return response.content

    def all_tracks(self, id_: str, type_: str = 'playlist',
                   progress: Optional[Callable[[int], None]] = None) -> list[dict[str, Any]]:
        """Полный список треков плейлиста/альбома постранично по offset."""
        collected: list[dict[str, Any]] = []
        offset = 0

        for _ in range(self._MAX_TRACKS_PAGES):
            data = self.tracks_page(type_, id_, offset)
            if data.get('success') is False:
                raise errors.ApiError(f"tracks page failed (status {data.get('statusCode')})")
            page = data.get('trackList') or []
            if not page:
                break

            collected.extend(page)
            offset += len(page)
            if progress:
                progress(len(collected))

        return collected
