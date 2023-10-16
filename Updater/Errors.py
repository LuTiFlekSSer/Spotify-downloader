__all__ = [
    'UpdateError',
    'UpdateCheckError'
]


class UpdateError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'UpdateError has been raised '


class UpdateCheckError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'UpdateCheckError has been raised '
