from typing import Any


class SpotiDlError(Exception):
    def __init__(self, *args: Any) -> None:
        self.mes = args[0] if args else None

    def __str__(self) -> str:
        return f'{self.mes}' if self.mes is not None else f'{self.__class__.__name__}'


class SessionError(SpotiDlError):
    """Не удалось получить сессию (Turnstile/`/session`)."""


class ApiError(SpotiDlError):
    """Ошибка запроса к spotidownloader API."""
