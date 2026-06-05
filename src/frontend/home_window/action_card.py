from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import CardWidget, FluentIcon, IconWidget, CaptionLabel, SubtitleLabel, FlowLayout

from src.utils.config import Config


class ActionCard(CardWidget):
    """Кликабельная карточка-действие (иконка + заголовок + описание)."""

    def __init__(self, icon: FluentIcon, title: str, description: str,
                 link_icon: bool = False, callback=None, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(196, 170)
        self._callback = callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self._iw_icon = IconWidget(self)
        self._iw_icon.setFixedSize(36, 36)
        self._apply_icon(icon)

        self._l_title = SubtitleLabel(self)
        self._l_title.setText(title)
        self._l_title.setWordWrap(True)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._l_desc = CaptionLabel(self)
        self._l_desc.setText(description)
        self._l_desc.setWordWrap(True)
        self._l_desc.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))

        layout.addWidget(self._iw_icon)
        layout.addSpacing(12)
        layout.addWidget(self._l_title)
        layout.addSpacing(4)
        layout.addWidget(self._l_desc)
        layout.addStretch()

        if link_icon:
            link = IconWidget(self)
            link.setIcon(FluentIcon.LINK.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)))
            link.setFixedSize(14, 14)
            link.move(170, 146)

        self.clicked.connect(self._on_clicked)

    def _apply_icon(self, icon: FluentIcon):
        self._iw_icon.setIcon(icon.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)))

    def _on_clicked(self):
        if self._callback:
            self._callback()

    def set_content(self, title: str, description: str):
        self._l_title.setText(title)
        self._l_desc.setText(description)

    def set_icon(self, icon: FluentIcon):
        self._apply_icon(icon)


class ActionCardView(QWidget):
    """Карточки-действия в FlowLayout — переносятся на новую строку, если не влезают."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._flow = FlowLayout(self, needAni=False)
        self._flow.setContentsMargins(0, 0, 0, 0)
        self._flow.setHorizontalSpacing(12)
        self._flow.setVerticalSpacing(12)

    def add_card(self, icon, title, description, link_icon=False, callback=None) -> ActionCard:
        card = ActionCard(icon, title, description, link_icon, callback, self)
        self._flow.addWidget(card)
        return card
