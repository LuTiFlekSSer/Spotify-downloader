from PySide6.QtWidgets import QApplication
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel, ProgressBar, InfoBar, InfoBarPosition

from src.backend.updater.updater import Updater
from src.backend.updater.workers import UpdateDownloadWorker
from src.locales.locales import Locales
from src.utils.utils import find_mega_parent, get_normalized_size


class UpdateDownloadDialog(MessageBoxBase):
    """Скачивание обновления с прогрессом. По завершении запускает установщик
    (новый .exe с -U) и закрывает приложение, чтобы освободить старый файл."""

    def __init__(self, updater: Updater, parent=None):
        super().__init__(parent)
        self._locales = Locales()
        self._updater = updater
        self._started = False

        self.widget.setMinimumWidth(440)

        self._title = SubtitleLabel(self._locales.get_string('downloading_update'))
        self._bar = ProgressBar(self)
        self._size_label = BodyLabel('')

        self.viewLayout.addWidget(self._title)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self._bar)
        self.viewLayout.addWidget(self._size_label)

        self.yesButton.hide()
        self.cancelButton.setText(self._locales.get_string('cancel'))

        self._worker = UpdateDownloadWorker(updater, self)
        self._worker.sig_progress.connect(self._on_progress)
        self._worker.sig_finished.connect(self._on_finished)
        self._worker.sig_error.connect(self._on_error)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._started:
            self._started = True
            self._worker.start()

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            self._bar.setValue(int(downloaded / total * 100))
            self._size_label.setText(
                f'{get_normalized_size(self._locales, downloaded)} / {get_normalized_size(self._locales, total)}')

    def _on_finished(self):
        self._title.setText(self._locales.get_string('installing_update'))
        self.cancelButton.setEnabled(False)
        try:
            self._updater.launch_installer()
            QApplication.quit()
        except Exception:
            self._fail('update_install_error')

    def _on_error(self, *_):
        self._fail('update_download_error')

    def _fail(self, key: str):
        InfoBar.error(title=self._locales.get_string('error'),
                      content=self._locales.get_string(key),
                      position=InfoBarPosition.BOTTOM_RIGHT, duration=4000,
                      parent=find_mega_parent(self))
        self.reject()
