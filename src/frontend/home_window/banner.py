from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import DisplayLabel, BodyLabel

from src.frontend.home_window.action_card import ActionCardView
from src.locales.locales import Locales
from src.utils.config import Config


class Banner(QWidget):
    """Шапка главного экрана: имя приложения + подзаголовок + лента действий."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName('w_banner')
        self._locales: Locales = Locales()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)   # без AlignLeft, чтобы лента действий заняла всю ширину

        self._l_app_name = DisplayLabel(self)
        self._l_app_name.setText(Config.APP_NAME)
        self._l_app_name.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._l_subtitle = BodyLabel(self)
        self._l_subtitle.setText(self._locales.get_string('home_subtitle'))
        self._l_subtitle.setTextColor(QColor(Config.GRAY_COLOR_600), QColor(Config.GRAY_COLOR_300))

        self.card_view: ActionCardView = ActionCardView(self)

        layout.addWidget(self._l_app_name)
        layout.addWidget(self._l_subtitle)
        layout.addSpacing(24)
        layout.addWidget(self.card_view)
