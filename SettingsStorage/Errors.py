__all__ = [
    'AlreadyExistsError',
    'NotFoundError'
]


class AlreadyExistsError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'AlreadyExistsError has been raised '


class NotFoundError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'NotFoundError has been raised '
