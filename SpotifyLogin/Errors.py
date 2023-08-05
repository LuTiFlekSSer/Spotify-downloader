__all__ = [
    'LoginDataError',
    'AuthorizationError'
]


class LoginDataError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'LoginDataError has been raised '


class AuthorizationError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'AuthorizationError has been raised '


class AuthorizationUrlError(Exception):
    def __init__(self, *args):
        if args:
            self.mes = args[0]
        else:
            self.mes = None

    def __str__(self):
        if self.mes is not None:
            return f'{self.mes}'

        return 'AuthorizationUrlError has been raised '
