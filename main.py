import CliUi
import CompatibilityChecker


def main():
    cc = CompatibilityChecker.CompatibilityChecker()

    if cc.need_db_update():
        cc.update_db()

    cli = CliUi.Cli()
    cli.start()


if __name__ == '__main__':
    main()
