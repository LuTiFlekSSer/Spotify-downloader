class SpotiDlError(Exception):
    def __init__(self, *args):
        self.mes = args[0] if args else None

    def __str__(self):
        return f'{self.mes}' if self.mes is not None else f'{self.__class__.__name__}'


class SessionError(SpotiDlError):
    """Не удалось получить сессию (Turnstile/`/session`)."""


class ApiError(SpotiDlError):
    """Ошибка запроса к spotidownloader API."""
