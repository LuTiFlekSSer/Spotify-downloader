import os
import sys
from types import TracebackType
from typing import Optional

# Nuitka standalone НЕ выставляет sys.frozen (в отличие от PyInstaller). Маркер компиляции
# Nuitka — модульная глобаль __compiled__ (пред-засевается до выполнения кода модуля; сам
# Nuitka читает sys.modules['__main__'].__compiled__). Без этого is_frozen() в собранном exe
# вернёт False, и самообновление сломается: launch_installer() кинет UpdateError, а hmi уйдёт
# в ветку "открыть браузер" вместо тихой установки. Эмулируем sys.frozen, чтобы все проверки
# getattr(sys, 'frozen', ...) (is_frozen, _app_dir) работали как в PyInstaller-сборке.
if '__compiled__' in globals():
    sys.frozen = True


def _app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


os.chdir(_app_dir())
sys.path.insert(0, _app_dir())


def main() -> None:
    # Обновление выполняет Inno-установщик (он закрывает приложение, обновляет файлы
    # на месте и перезапускает) — старый механизм самоподмены `-U` удалён.
    import logging
    from src.utils.utils import setup_logging

    setup_logging()

    def _log_excepthook(exc_type: type[BaseException], exc: BaseException, tb: Optional[TracebackType]) -> None:
        logging.getLogger('uncaught').error('uncaught exception', exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _log_excepthook
    logging.getLogger('startup').info('app start, frozen=%s', getattr(sys, 'frozen', False))

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
