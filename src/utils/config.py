from os import getenv

from src.utils.singleton import Singleton


class Config(metaclass=Singleton):
    APP_NAME = 'Spotify Downloader'

    GITHUB_URL = 'https://github.com/LuTiFlekSSer/Spotify-downloader'
    GITHUB_RELEASES_URL = 'https://api.github.com/repos/LuTiFlekSSer/Spotify-downloader/releases/latest'
    GITHUB_RELEASES_HTML = 'https://github.com/LuTiFlekSSer/Spotify-downloader/releases/latest'

    SPLASH_SCREEN_TIME = 2

    LOCALES_PATH = 'src/locales/locales.json'

    # %APPDATA%/Spotify Downloader/ — на Windows регистронезависимо совпадает со старой папкой,
    # поэтому новый database.db лежит рядом со старым settings.db (миграция в Фазе 1).
    APP_DATA_DIR = f"{getenv('APPDATA')}/{APP_NAME}/"
    DB_PATH = APP_DATA_DIR
    DB_FILENAME = 'database.db'
    OLD_SETTINGS_DB = f"{getenv('APPDATA')}/Spotify downloader/settings.db"
    SPOTIPY_CACHE = f"{getenv('APPDATA')}/Spotify downloader/.cache"

    WINDOW_ICON = 'icons/icon.ico'

    # --- download-API spotidownloader.com (см. REWRITE_PLAN.md §4) ---
    SPOTIDL_BASE = 'https://api.spotidownloader.com'
    SPOTIDL_SITE = 'https://spotidownloader.com'
    TURNSTILE_PAGE = 'https://spotidownloader.com/en'
    # стабильная ссылка-праймер: вставляется на сайт, чтобы клик Download инициировал сессию
    SESSION_PRIMER_URL = 'https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT'
    SESSION_REFRESH_MARGIN = 30.0       # обновлять сессию за N секунд до exp
    TURNSTILE_HEADLESS = True           # дефолт; флаг — в настройках
    USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36')

    # --- timings ---
    THREAD_SLEEP = 0.01
    UPDATE_INTERVAL = 0.1

    # --- gray palette (для theme-aware текста, как в референсе) ---
    GRAY_COLOR_50 = '#F3F3F3'
    GRAY_COLOR_100 = '#DDDDDD'
    GRAY_COLOR_200 = '#C6C6C6'
    GRAY_COLOR_300 = '#B0B0B0'
    GRAY_COLOR_400 = '#9B9B9B'
    GRAY_COLOR_500 = '#868686'
    GRAY_COLOR_600 = '#727272'
    GRAY_COLOR_700 = '#5E5E5E'
    GRAY_COLOR_800 = '#4B4B4B'
    GRAY_COLOR_900 = '#393939'
