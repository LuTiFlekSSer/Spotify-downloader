__all__ = [
    'Locales',
]

import ctypes
import json
import locale

from src.backend.db.data_base import DataBase
from src.locales import errors
from src.utils.config import Config
from src.utils.singleton import Singleton


class Locales(metaclass=Singleton):
    with open(Config.LOCALES_PATH, encoding='utf-8') as _file:
        _locales = json.load(_file)

    _language = None

    def __init__(self) -> None:
        super().__init__()

        db = DataBase()
        language = db.get_setting('language')

        if language == 'None':
            language = self._detect_system_language()
            db.set_setting('language', language)

        self.set_language(language)

    @staticmethod
    def _detect_system_language() -> str:
        try:
            ui_lang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            system_language = locale.windows_locale[ui_lang]
        except Exception:
            system_language = ''

        return 'ru' if system_language == 'ru_RU' else 'en'

    @staticmethod
    def get_string(string_name: str) -> str:
        if not isinstance(string_name, str):
            raise TypeError

        if Locales._language is None:
            raise errors.LanguageNotSetError

        try:
            return Locales._locales['strings'][string_name][Locales._language]
        except Exception:
            raise errors.GetStringError(string_name)

    @staticmethod
    def set_language(language: str) -> None:
        if not isinstance(language, str):
            raise TypeError

        if language not in Locales._locales['languages']:
            raise errors.SetLocaleError

        Locales._language = language

    @staticmethod
    def get_languages() -> dict[str, str]:
        return Locales._locales['languages']
