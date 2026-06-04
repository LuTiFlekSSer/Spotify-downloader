from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, TitleLabel, BodyLabel


class PlaceholderPage(ScrollArea):
    """Временная страница-заглушка для навигации каркаса (Фаза 0).
    Заменяется реальными окнами в Фазе 4."""

    def __init__(self, object_name: str, title: str, subtitle: str = '', parent=None):
        super().__init__(parent=parent)
        self.setObjectName(object_name.replace(' ', '-'))

        self._w_view: QWidget = QWidget(self)
        self._w_view.setObjectName('w_view')
        self._vl_view: QVBoxLayout = QVBoxLayout(self._w_view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self._w_view)
        self.setWidgetResizable(True)

        self._vl_view.setContentsMargins(28, 28, 28, 28)
        self._vl_view.setSpacing(12)
        self._vl_view.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._vl_view.addWidget(TitleLabel(title))
        if subtitle:
            self._vl_view.addWidget(BodyLabel(subtitle))
