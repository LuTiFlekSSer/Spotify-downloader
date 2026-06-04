import os
from urllib.parse import urlparse, parse_qs

from spotipy import Spotify, SpotifyOAuth, CacheFileHandler, SpotifyOauthError

from src.backend.db.data_base import DataBase
from src.backend.spotify import errors
from src.utils.config import Config
from src.utils.singleton import Singleton


class SpotifySession(metaclass=Singleton):
    """Spotify OAuth (Authorization Code) с переходом на refresh-token.

    В отличие от старого приложения (которое каждый запуск заново обменивало
    одноразовый `code`), здесь spotipy сам обновляет access-token по refresh-token
    из CacheFileHandler — повторный вход не требуется.
    """

    SCOPE = 'user-library-read'

    def __init__(self):
        self._db: DataBase = DataBase()
        self._auth = None
        self._client = None
        try:
            self._build_auth()          # на старте не валим приложение из-за битых кредов
        except errors.LoginDataError:
            self._auth = None

    def _build_auth(self):
        self._client = None
        client_id = self._db.get_setting('client_id')
        client_secret = self._db.get_setting('client_secret')
        redirect_uri = self._db.get_setting('redirect_uri')

        if not (client_id and client_secret and redirect_uri):
            self._auth = None
            return

        try:
            self._auth = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=self.SCOPE,
                cache_handler=CacheFileHandler(cache_path=Config.SPOTIPY_CACHE),
                open_browser=False,
            )
        except Exception:
            self._auth = None
            raise errors.LoginDataError

    # ---------- состояние ----------
    def is_configured(self) -> bool:
        return self._auth is not None

    def is_authenticated(self) -> bool:
        if self._auth is None:
            return False
        try:
            token = self._auth.cache_handler.get_cached_token()
            return token is not None and self._auth.validate_token(token) is not None
        except Exception:
            return False

    # ---------- логин ----------
    def get_authorization_url(self) -> str:
        if self._auth is None:
            raise errors.NotConfiguredError
        return self._auth.get_authorize_url()

    def complete_login(self, redirect_url: str):
        """Принимает URL, на который Spotify перенаправил после авторизации,
        извлекает ?code= и обменивает на токен (он же кэшируется с refresh-token)."""
        if self._auth is None:
            raise errors.NotConfiguredError

        query = parse_qs(urlparse(redirect_url).query)
        if 'code' not in query:
            raise errors.AuthUrlError

        try:
            self._auth.get_access_token(query['code'][0], check_cache=False)
        except SpotifyOauthError:
            raise errors.AuthError

        self._client = None

    def get_client(self) -> Spotify:
        if not self.is_authenticated():
            raise errors.NotAuthenticatedError
        if self._client is None:
            self._client = Spotify(auth_manager=self._auth)
        return self._client

    # ---------- управление кредами ----------
    def set_credentials(self, client_id: str, client_secret: str, redirect_uri: str):
        self._db.set_setting('client_id', client_id.strip())
        self._db.set_setting('client_secret', client_secret.strip())
        self._db.set_setting('redirect_uri', redirect_uri.strip())
        self._build_auth()

    def logout(self):
        try:
            os.remove(Config.SPOTIPY_CACHE)
        except OSError:
            pass
        self._build_auth()
