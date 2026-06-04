from threading import Event

from src.utils.singleton import Singleton


class GlobalFlags(metaclass=Singleton):
    def __init__(self):
        self.stop_event: Event = Event()      # завершение фоновых потоков
        self.is_running: Event = Event()      # идёт загрузка — блокирует закрытие окна
        self.is_syncing: Event = Event()      # идёт синхронизация
        self.modal_open: Event = Event()      # открыта модалка
