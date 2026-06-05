from PySide6.QtCore import QThread, Signal

from src.backend.updater.updater import Updater


class UpdateCheckWorker(QThread):
    sig_result = Signal(object)   # ReleaseInfo | None
    sig_error = Signal(str)

    def __init__(self, updater: Updater, parent=None):
        super().__init__(parent)
        self._updater = updater

    def run(self):
        try:
            self.sig_result.emit(self._updater.check())
        except Exception as e:
            self.sig_error.emit(str(e))


class UpdateDownloadWorker(QThread):
    sig_progress = Signal(int, int)   # скачано, всего (байт)
    sig_finished = Signal()
    sig_error = Signal(str)

    def __init__(self, updater: Updater, parent=None):
        super().__init__(parent)
        self._updater = updater

    def run(self):
        try:
            self._updater.start_download()
            for downloaded, total in self._updater.download():
                self.sig_progress.emit(downloaded, total)
            self.sig_finished.emit()
        except Exception as e:
            self.sig_error.emit(str(e))
