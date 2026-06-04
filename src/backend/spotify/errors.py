class _SpotifyError(Exception):
    def __init__(self, *args):
        self.mes = args[0] if args else None

    def __str__(self):
        return f'{self.mes}' if self.mes is not None else f'{self.__class__.__name__}'


class LoginDataError(_SpotifyError):
    """Некорректные/битые данные приложения Spotify (client_id/secret/uri)."""


class NotConfiguredError(_SpotifyError):
    """Не заданы client_id/client_secret/redirect_uri."""


class NotAuthenticatedError(_SpotifyError):
    """Нет валидного токена — нужен вход."""


class AuthUrlError(_SpotifyError):
    """В ссылке-редиректе нет параметра ?code=."""


class AuthError(_SpotifyError):
    """Ошибка обмена кода на токен."""


class TracksGetError(_SpotifyError):
    """Ошибка при получении треков из Spotify."""
