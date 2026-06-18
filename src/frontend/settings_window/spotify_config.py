from os import cpu_count

from qfluentwidgets import (QConfig, ConfigItem, BoolValidator, OptionsConfigItem,
                            OptionsValidator, RangeConfigItem, RangeValidator)

from src.backend.db.data_base import DataBase


class SpotifyConfig(QConfig):
    """QConfig поверх нашей DataBase: значения грузятся из settings и пишутся
    обратно в settings при каждом set() (QConfig.set вызывает save()).

    Используется как модуль-глобал `spotify_config` — это де-факто синглтон,
    без метакласс-гимнастики (в PySide6 метакласс QConfig конфликтует с нашим)."""

    app_theme = OptionsConfigItem('settings', 'theme', 'AUTO', OptionsValidator(['DARK', 'LIGHT', 'AUTO']))
    app_language = OptionsConfigItem('settings', 'language', 'en', OptionsValidator(['ru', 'en']))
    download_threads = RangeConfigItem('settings', 'threads', 4, RangeValidator(1, (cpu_count() or 4) * 2))
    overwrite_tracks = ConfigItem('settings', 'overwrite_tracks', False, BoolValidator())
    auto_compare = ConfigItem('settings', 'auto_compare', True, BoolValidator())
    auto_update = ConfigItem('settings', 'auto_update', True, BoolValidator())
    turnstile_headless = ConfigItem('settings', 'turnstile_headless', True, BoolValidator())
    download_dir = ConfigItem('settings', 'download_dir', '')

    def __init__(self) -> None:
        super().__init__()
        self._db = DataBase()
        self._load()

    def reload(self) -> None:
        """Перечитать значения из DataBase. Нужно, т.к. `spotify_config` создаётся на
        этапе импорта (до того как SingletonStorage/Locales определят системный язык и
        запишут его в settings) — иначе комбобокс языка покажет дефолт 'en', хотя
        интерфейс уже на русском. Вызывается при сборке окна настроек (после Locales)."""
        self._load()

    def _load(self) -> None:
        g = self._db.get_setting

        theme = g('theme')
        self.app_theme.value = theme if theme in ('DARK', 'LIGHT', 'AUTO') else 'AUTO'

        lang = g('language')
        self.app_language.value = lang if lang in ('ru', 'en') else 'en'

        try:
            self.download_threads.value = int(g('threads'))
        except (ValueError, TypeError):
            self.download_threads.value = cpu_count() or 4

        self.overwrite_tracks.value = g('overwrite_tracks') == 'True'
        self.auto_compare.value = g('auto_compare') == 'True'
        self.auto_update.value = g('auto_update') == 'True'
        self.turnstile_headless.value = g('turnstile_headless') == 'True'
        self.download_dir.value = g('download_dir')

    def save(self) -> None:
        # пишем в DataBase вместо json-файла QConfig
        for key, value in self.toDict()['settings'].items():
            self._db.set_setting(key, str(value))


spotify_config = SpotifyConfig()
