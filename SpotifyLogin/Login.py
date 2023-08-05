__all__ = [
    'Login'
]

from spotipy import Spotify, SpotifyOAuth, SpotifyOauthError
from os import environ

from SpotifyLogin import Errors
from urllib.parse import urlparse, parse_qs


class Login:
    _scope = 'user-library-read'

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        if client_id is None or client_secret is None or redirect_uri is None:
            try:
                client_id = environ['SPOTIPY_CLIENT_ID']
                client_secret = environ['SPOTIPY_CLIENT_SECRET']
                redirect_uri = environ['SPOTIPY_REDIRECT_URI']

            except KeyError:
                raise Errors.LoginDataError('No login parameters are specified')

        if not (isinstance(client_id, str) and isinstance(client_secret, str) and isinstance(redirect_uri, str)):
            raise TypeError

        self._auth = SpotifyOAuth(scope=Login._scope,
                                  client_id=client_id,
                                  client_secret=client_secret,
                                  redirect_uri=redirect_uri
                                  )

        self._spotify = None
        self._auth_url = self._auth.get_authorize_url()

    def login_with_authorization_code(self, url):
        if not isinstance(url, str):
            raise TypeError

        query = parse_qs(urlparse(url).query)

        if 'code' not in query:
            raise Errors.AuthorizationUrlError

        code = query['code'][0]

        try:
            self._spotify = Spotify(auth=self._auth.get_access_token(code)['access_token'])
        except SpotifyOauthError:
            raise Errors.AuthorizationError

    def get_authorization_url(self):
        return self._auth_url

    def get_client(self):
        return self._spotify
