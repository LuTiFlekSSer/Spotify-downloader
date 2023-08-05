__all__ = [
    'TracksGetError',
    'ClientError'
]


class TracksGetError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'TracksGetError has been raised '


class ClientError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'ClientError has been raised '
