__all__ = [
    'CompatibilityChecker'
]

import SettingsStorage
import Version
from Ui import Utils


class CompatibilityChecker:
    def __init__(self):
        self._settings = SettingsStorage.Settings()
        self._db_version = self._get_db_version()

    def _get_db_version(self):
        try:
            ver = self._settings.get_setting('version')
        except SettingsStorage.NotFoundError:
            ver = '1.0.0'

        return ver

    def need_db_update(self):
        return Utils.compare_versions(self._db_version, Version.__version__)

    def update_db(self):
        self._update_to_1_2_0()
        self._update_to_1_2_2()

        if self.need_db_update():
            self._settings.change_setting('version', Version.__version__)

    def _update_to_1_2_2(self):
        if Utils.compare_versions(self._db_version, '1.2.2'):
            self._settings.change_setting('version', '1.2.2')
            self._settings.create_setting('overwrite_tracks', 'False')

            self._db_version = '1.2.2'

    def _update_to_1_2_0(self):
        if Utils.compare_versions(self._db_version, '1.2.0'):
            self._settings.create_setting('version', '1.2.0')
            self._settings.create_setting('auto_update', 'True')

            self._db_version = '1.2.0'
