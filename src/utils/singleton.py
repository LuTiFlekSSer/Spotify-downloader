from weakref import WeakValueDictionary


class Singleton(type):
    _instances: WeakValueDictionary[type, object] = WeakValueDictionary()

    def __call__(cls, *args: object, **kwargs: object) -> object:
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
