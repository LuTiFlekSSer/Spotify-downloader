__all__ = [
    'GetStringError',
    'LanguageNotSetError',
    'SetLocaleError',
]


class _LocaleError(Exception):
    def __init__(self, *args: object) -> None:
        self.mes = args[0] if args else None

    def __str__(self) -> str:
        if self.mes is not None:
            return f'{self.mes}'
        return f'{self.__class__.__name__} has been raised'


class GetStringError(_LocaleError):
    pass


class SetLocaleError(_LocaleError):
    pass


class LanguageNotSetError(_LocaleError):
    pass
