__all__ = [
    'Update'
]

import Updater
import CompatibilityChecker
import time
import Utils
import SettingsStorage


class Update:
    def __init__(self):
        self._cc = CompatibilityChecker.CompatibilityChecker()

        self._updater = Updater.Updater()

    def start(self):
        if self._cc.need_db_update():
            self._cc.update_db()

        updater = Updater.Updater()

        ss = SettingsStorage.Settings()

        if ss.get_setting('auto_update') == 'True':
            try:
                if updater.need_app_update():
                    print(Utils.green('Обнаружено обновление'))
                    print('Скачать?', Utils.yellow('(да - y, нет - n)'))
                    while True:
                        match Utils.g_input('> '):
                            case 'y':
                                updater.download_update()
                                updater.install_update()
                                break
                            case 'n':
                                print(Utils.green('Загрузка отменена'))
                                time.sleep(1)
                                break
                            case _:
                                print(Utils.red('Ошибка ввода'))

            except Updater.UpdateCheckError:
                print(Utils.red('Ошибка при проверке обновлений'))
                time.sleep(1)

            except Updater.UpdateError:
                print(Utils.red('Ошибка при обновлении'))
                time.sleep(1)

            except Exception as ex:
                print(Utils.red('Ошибка при загрузке обновления'), ex)
                time.sleep(1)
