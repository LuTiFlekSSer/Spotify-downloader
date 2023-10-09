__all__ = [
    'CompatibilityChecker'
]

import SettingsStorage
import version


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

    def _compare_versions(self, new_version):
        if self._db_version.split('.') < new_version.split('.'):
            return True

        return False

    def need_db_update(self):
        return self._compare_versions(version.__version__)

    def update_db(self):
        self._update_to_1_2_0()

    def _update_to_1_2_0(self):
        if self._compare_versions('1.2.0'):
            self._settings.create_setting('version', '1.2.0')

            self._db_version = '1.2.0'
