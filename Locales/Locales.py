__all__ = [
    'Locales'
]

import json
from Locales import Errors
from Ui import Utils


class Locales:
    with open(Utils.resource_path('Locales/locales.json'), encoding='utf-8') as file:
        _locales = json.load(file)

    _language = None

    @staticmethod
    def get_string(string_name):
        if not isinstance(string_name, str):
            raise TypeError

        if Locales._language is None:
            raise Errors.LanguageNotSetError

        try:
            return Locales._locales['strings'][string_name][Locales._language]
        except Exception:
            raise Errors.GetStringError

    @staticmethod
    def set_language(language):
        if not isinstance(language, str):
            raise TypeError

        if language not in Locales._locales['languages']:
            raise Errors.SetLocaleError

        Locales._language = language

    @staticmethod
    def get_languages():
        return Locales._locales['languages']
