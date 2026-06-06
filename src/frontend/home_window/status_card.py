from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (InfoBarIcon, IconWidget, StrongBodyLabel, CaptionLabel,
                            TitleLabel, FlowLayout, SimpleCardWidget)

from src.utils.config import Config


class StatusCard(SimpleCardWidget):
    """Статус-карточка: иконка ок/внимание + заголовок + описание."""

    def __init__(self, title: str, description: str, ok: bool, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setFixedSize(300, 80)

        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(20, 12, 16, 12)
        h_layout.setSpacing(16)

        self._iw_icon = IconWidget(self)
        self._iw_icon.setIcon(InfoBarIcon.SUCCESS if ok else InfoBarIcon.WARNING)
        self._iw_icon.setFixedSize(28, 28)

        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._l_title = StrongBodyLabel(self)
        self._l_title.setText(title)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._l_desc = CaptionLabel(self)
        self._l_desc.setText(description)
        self._l_desc.setWordWrap(True)
        self._l_desc.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))

        v_layout.addWidget(self._l_title)
        v_layout.addWidget(self._l_desc)

        h_layout.addWidget(self._iw_icon)
        h_layout.addLayout(v_layout, 1)


class StatusCardView(QWidget):
    """Заголовок секции + сетка статус-карточек (FlowLayout)."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._cards: list[StatusCard] = []

        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(14)

        self._l_title = TitleLabel(self)
        self._l_title.setText(title)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._flow = FlowLayout()
        self._flow.setContentsMargins(0, 0, 0, 0)
        self._flow.setHorizontalSpacing(16)
        self._flow.setVerticalSpacing(16)

        v_layout.addWidget(self._l_title)
        v_layout.addLayout(self._flow, 1)

    def set_cards(self, cards: list[tuple[str, str, bool]]) -> None:
        self._flow.takeAllWidgets()
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards = []

        for title, description, ok in cards:
            card = StatusCard(title, description, ok, self)
            self._flow.addWidget(card)
            self._cards.append(card)
