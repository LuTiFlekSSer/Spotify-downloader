import base64
import json
import logging
import time
from threading import RLock
from typing import Callable

import requests
from PySide6.QtCore import QObject, Signal

from src.backend.db.data_base import DataBase
from src.backend.spotidl import constants, errors
from src.backend.spotidl.turnstile import SessionMinter
from src.utils.config import Config
from src.utils.singleton import Singleton


def read_exp_from_jwt(jwt: str) -> float:
    """Достаёт `exp` (epoch) из payload JWT без проверки подписи."""
    payload = jwt.split('.')[1]
    payload += '=' * (-len(payload) % 4)            # padding для base64url
    data = json.loads(base64.urlsafe_b64decode(payload))
    return float(data['exp'])


class SpotiSession(metaclass=Singleton):
    """Глобальное хранилище сессионного ключа spotidownloader (Bearer-JWT, ~10 мин).

    Шарится всеми потоками загрузки. get_token() обновляет сессию по истечении
    срока single-flight: N потоков на истёкшем ключе блокируются на RLock и
    делают ровно ОДИН рефреш (дорогой — поднимает браузер), затем переиспользуют
    свежий токен. Рефреш = решить Turnstile -> POST /session -> распарсить exp."""

    class Events(QObject):
        sig_refreshing = Signal()
        sig_refreshed = Signal()
        sig_refresh_failed = Signal(str)

    events = Events()

    def __init__(self) -> None:
        self._lock = RLock()
        self._token: str = ''
        self._exp: float = 0.0
        self._margin: float = Config.SESSION_REFRESH_MARGIN
        self._provider: Callable[[], str] = self._default_provider     # () -> jwt str (инъектируется в тестах)

    def set_provider(self, provider: Callable[[], str]) -> None:
        with self._lock:
            self._provider = provider

    def _is_valid(self) -> bool:
        return bool(self._token) and time.time() < self._exp - self._margin

    @property
    def is_valid(self) -> bool:
        with self._lock:
            return self._is_valid()

    def get_token(self) -> str:
        with self._lock:
            if not self._is_valid():
                self._refresh_locked()
            return self._token

    def force_refresh(self, stale_token: str | None = None) -> None:
        """Обновление по 401/403. Single-flight: если другой поток уже обновил
        токен (текущий отличается от переданного устаревшего) — капчу повторно
        НЕ решаем, просто используем свежий."""
        with self._lock:
            if stale_token is not None and self._token and self._token != stale_token:
                return
            self._refresh_locked()

    def clear(self) -> None:
        with self._lock:
            self._token = ''
            self._exp = 0.0

    def _refresh_locked(self) -> None:
        self.events.sig_refreshing.emit()
        try:
            jwt = self._provider()
            self._token = jwt
            self._exp = read_exp_from_jwt(jwt)
            self.events.sig_refreshed.emit()
        except Exception as e:
            self._token = ''
            self._exp = 0.0
            logging.getLogger(__name__).exception('session refresh failed (Turnstile/Camoufox/network)')
            self.events.sig_refresh_failed.emit(str(e))
            raise errors.SessionError(str(e))

    def _default_provider(self) -> str:
        headless = DataBase().get_setting('turnstile_headless') == 'True'
        cf_token = SessionMinter(headless=headless).solve()     # браузер: только cf-токен, затем закрывается

        response = requests.post(constants.SESSION_URL, json={'token': cf_token},
                                 headers=constants.api_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get('success') or not data.get('token'):
            raise errors.SessionError('session token was not granted')
        return data['token']
