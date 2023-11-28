import Ui
import ErrorSaver
from Ui import Utils
import os


def main():
    cli = Ui.Ui()
    try:
        cli.start()
    except Exception:
        es = ErrorSaver.ErrorSaver()

        path = es.save_log()

        os.system('cls')
        print(Utils.red(f'{Utils.Colors.BLINK}Произошла ошибка во время работы программы\n'
                        f'Подробности в файле: "{path}"'))
        input('\nНажмите Enter для выхода')


if __name__ == '__main__':
    main()
