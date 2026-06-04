from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QWheelEvent
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (CardWidget, FluentIcon, IconWidget, CaptionLabel,
                            SingleDirectionScrollArea, SubtitleLabel)

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


class ActionCardView(SingleDirectionScrollArea):
    """Горизонтальная лента карточек-действий."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Orientation.Horizontal)
        self._w_view = QWidget(self)
        self._w_view.setObjectName('w_view')

        self._layout = QHBoxLayout(self._w_view)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.setWidget(self._w_view)
        self.setWidgetResizable(True)
        self.setFixedHeight(186)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        try:
            self.enableTransparentBackground()
        except Exception:
            pass

    def add_card(self, icon, title, description, link_icon=False, callback=None) -> ActionCard:
        card = ActionCard(icon, title, description, link_icon, callback, self)
        self._layout.addWidget(card, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    def wheelEvent(self, e: QWheelEvent):
        if self.horizontalScrollBar().maximum() == 0:
            e.ignore()
        else:
            super().wheelEvent(e)
