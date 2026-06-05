import os
import sys


def _app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


os.chdir(_app_dir())
sys.path.insert(0, _app_dir())


def main():
    # самоподмена при обновлении: новый .exe запущен с `-U "<старый путь>"`.
    # Копируем себя поверх старого файла и перезапускаем его — до всего остального.
    if '-U' in sys.argv:
        idx = sys.argv.index('-U')
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]
            import subprocess
            from src.backend.updater.updater import Updater
            try:
                Updater.install_update(target)
            except Exception:
                pass
            try:
                subprocess.Popen([target], creationflags=subprocess.CREATE_NEW_CONSOLE)
            except Exception:
                pass
        sys.exit(0)

    from src.frontend.instance_manager import InstanceManager

    instance_manager = InstanceManager()

    if not instance_manager.try_acquire_lock():
        # вторичный экземпляр: пробросить аргумент (ссылку) в работающее окно
        if len(sys.argv) > 1:
            instance_manager.send('open', sys.argv[1])
        sys.exit(0)

    from src.frontend.hmi import create_ui
    from src.singleton_storage import SingletonStorage

    SingletonStorage()

    app, window = create_ui()

    instance_manager.start_server()
    app.aboutToQuit.connect(instance_manager.release_lock)
    instance_manager.sig_external_command.connect(window.sig_external_command.emit)

    if len(sys.argv) > 1:
        window.sig_external_command.emit('open', sys.argv[1])

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
