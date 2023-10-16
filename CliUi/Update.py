__all__ = [
    'Update'
]

import Updater
import CompatibilityChecker
import time
import Utils
import SettingsStorage
import subprocess
from progress.spinner import PixelSpinner
import threading
import os


def _print_greeting():
    os.system('cls')
    print(Utils.cyan('------------------------------------\n'
                     '| SPOTIFY DOWNLOADER WELCOMES YOU! |\n'
                     '------------------------------------'))


class Update:
    def __init__(self):
        self._cc = CompatibilityChecker.CompatibilityChecker()

        self._updater = Updater.Updater()

        self._stop_spinner = False

    def start(self):
        if self._cc.need_db_update():
            self._cc.update_db()

        updater = Updater.Updater()

        ss = SettingsStorage.Settings()

        if ss.get_setting('auto_update') == 'True':
            try:
                if updater.need_app_update():
                    _print_greeting()

                    print(Utils.green('Обнаружено обновление'))
                    print('Скачать?', Utils.yellow('(да - y, нет - n)'))

                    while True:
                        match Utils.g_input('> '):
                            case 'y':
                                updater.download_update()

                                _print_greeting()

                                print(Utils.green('Загрузка завершена'))
                                time.sleep(1)

                                updater.start_update()
                                return True
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

        return False

    def install(self, path_to_exe):
        _print_greeting()

        t = threading.Thread(target=self._spinner)
        t.start()
        time.sleep(2)

        try:
            self._updater.install_update(path_to_exe)
        except Updater.UpdateError:
            self._stop_spinner = True
            t.join()
            _print_greeting()

            print(Utils.red('Ошибка при установке обновления\n'))
            print(f'Возможно, поможет ручная замена файла:\n'
                  f'{Utils.yellow(path_to_exe)}\n'
                  f'На файл обновления:\n'
                  f'{Utils.yellow(Updater.get_executable_path())}')

            input('\nНажми Enter для выхода')

            return

        self._stop_spinner = True
        t.join()

        _print_greeting()

        print(Utils.green('Обновление установлено'))
        time.sleep(1)

        subprocess.Popen(path_to_exe, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _spinner(self):
        spinner = PixelSpinner(Utils.Colors.YELLOW + 'Установка обновления ')

        spinner.start()

        while not self._stop_spinner:
            time.sleep(0.5)
            spinner.next()

        spinner.finish()
