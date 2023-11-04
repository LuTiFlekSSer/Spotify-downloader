import CliUi
import ErrorSaver
from CliUi import Utils
import os


def main():
    cli = CliUi.Cli()
    try:
        cli.start()
    except Exception:
        es = ErrorSaver.ErrorSaver()

        path = es.save_log()

        os.system('cls')
        print(Utils.red(f'{Utils.Colors.BLINK}Произошла ошибка во время работы программы\n'
                        f'Подробности в файле: "{path}"'))


if __name__ == '__main__':
    main()
