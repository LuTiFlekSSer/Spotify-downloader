__all__ = [
    'Update'
]

import Updater
import CompatibilityChecker


class Update:
    def __init__(self):
        self._cc = CompatibilityChecker.CompatibilityChecker()

        self._updater = Updater.Updater()

    def start(self):
        if self._cc.need_db_update():
            self._cc.update_db()

        updater = Updater.Updater()

        try:
            if updater.need_app_update():
                updater.download_update()
                updater.install_update()
        except Updater.UpdateCheckError:
            pass
        except Updater.UpdateError:
            pass
        except Exception:
            pass
