from threading import Lock
from typing import Any, Optional

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QScrollArea


class PagedListView(QWidget):
    """Виртуализированный список: переиспользует небольшой пул виджетов-строк и
    рендерит одну «страницу» строк по высоте вьюпорта. Виджет-строка должен иметь
    метод set_data(data). Перенесён из референса Encryption_app (PyQt5 -> PySide6)."""

    page_changed: Signal = Signal()
    pagination_changed: Signal = Signal(int, int)
    item_hidden: Signal = Signal(object)        # строка попросила «скрыть» (если умеет sig_hide)

    def __init__(self, item_widget_class: type[QWidget], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._lock = Lock()
        self._item_widget_class = item_widget_class
        self._rows_hideable: bool = False

        self._items: dict[Any, Any] = {}
        self._keys: list[Any] = []
        self._item_widgets: list[QWidget] = []

        self._first_visible_index: int = 0
        self._visible_count: int = 0
        self._last_pagination_state: tuple[int, int] = (-1, -1)
        self._pending_pagination_emit: bool = False

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Прозрачный фон: и сам QScrollArea, и его viewport (это отдельный QWidget — qss
        # `QScrollArea{background}` его НЕ красит, поэтому по умолчанию он белый/Base).
        # Иначе на чистой машине (без эффекта Mica) под таблицей видна белая подложка.
        self._scroll_area.setStyleSheet('QScrollArea{border:none;background:transparent;}')
        self._scroll_area.viewport().setStyleSheet('background:transparent;')
        self._layout.addWidget(self._scroll_area)

        self._container = QWidget(self)
        self._container.setObjectName('w_view')
        self._container.setStyleSheet('#w_view{background:transparent;}')
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setSpacing(8)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll_area.setWidget(self._container)

    @property
    def items_dict(self) -> dict[Any, Any]:
        with self._lock:
            return self._items

    def set_items(self, items: dict[Any, Any]) -> None:
        with self._lock:
            self._items = items
            self._keys = list(items.keys())
            self._first_visible_index = 0
        self.update_view()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.update_view()
        return super().resizeEvent(event)

    def update_view(self) -> None:
        if not self._items:
            self._update_widgets()      # модель пуста -> спрятать ранее показанные строки
            return

        sample = self._item_widgets[0] if self._item_widgets else self._item_widget_class()
        if not self._item_widgets:
            sample.setParent(self)
            sample.hide()

        height_available = self._scroll_area.viewport().height()
        item_height = sample.height() + self._container_layout.spacing()
        new_visible_count = max(1, height_available // max(1, item_height))

        with self._lock:
            while len(self._item_widgets) < new_visible_count:
                widget = self._item_widget_class()
                if hasattr(widget, 'sig_hide'):
                    widget.sig_hide.connect(self.item_hidden)
                if hasattr(widget, 'set_hideable'):
                    widget.set_hideable(self._rows_hideable)
                self._container_layout.addWidget(widget)
                self._item_widgets.append(widget)

            self._visible_count = new_visible_count

            viewport_width = self._scroll_area.viewport().width()
            margins = self._container_layout.contentsMargins()
            widget_max_width = viewport_width - (margins.left() + margins.right())
            for widget in self._item_widgets:
                widget.setMaximumWidth(widget_max_width)

        self._update_widgets()
        self._emit_pagination_changed()

    def set_hideable(self, value: bool) -> None:
        """Показать/скрыть кнопки «скрыть» во всех строках (если строка их поддерживает)."""
        self._rows_hideable = value
        with self._lock:
            for widget in self._item_widgets:
                if hasattr(widget, 'set_hideable'):
                    widget.set_hideable(value)

    def _update_widgets(self) -> None:
        with self._lock:
            start = self._first_visible_index
            end = min(len(self._keys), start + self._visible_count)

            for i, widget in enumerate(self._item_widgets):
                data_index = start + i
                if data_index < end:
                    item_data = self._items[self._keys[data_index]]
                    if hasattr(widget, 'set_data'):
                        widget.set_data(item_data)
                    else:
                        raise AttributeError('item widget must implement set_data')
                    widget.show()
                else:
                    widget.hide()

        self.page_changed.emit()

    def add_item(self, key: Any, data: Any) -> None:
        with self._lock:
            if key not in self._items:
                self._items[key] = data
                self._keys.insert(0, key)
        self.update_view()

    def update_item(self, key: Any, data: Any = None) -> None:
        """Обновить данные строки (если она видима — перерисовать)."""
        with self._lock:
            if key not in self._items:
                return
            if data is not None:
                self._items[key] = data
        self._update_widgets()

    def remove_item(self, key: Any) -> bool:
        with self._lock:
            if key not in self._items:
                return False
            del self._items[key]
            self._keys.remove(key)
            if self._first_visible_index >= len(self._keys):
                self._first_visible_index = max(0, len(self._keys) - self._visible_count)
        if not self._keys:
            self.clear_items()
        else:
            self.update_view()
        return True

    def clear_items(self) -> None:
        with self._lock:
            self._items.clear()
            self._keys.clear()
            self._first_visible_index = 0
        self._update_widgets()

    def get_total_items(self) -> int:
        with self._lock:
            return len(self._items)

    def set_page(self, page_number: int) -> None:
        if self._visible_count == 0:
            self.update_view()
        with self._lock:
            max_page = max(0, (len(self._items) - 1) // max(1, self._visible_count))
            page_number = max(0, min(page_number, max_page))
            self._first_visible_index = page_number * self._visible_count
        self._update_widgets()

    def get_current_page(self) -> int:
        if self._visible_count == 0:
            self.update_view()
        with self._lock:
            return self._first_visible_index // max(1, self._visible_count)

    def get_total_pages(self) -> int:
        if self._visible_count == 0:
            self.update_view()
        with self._lock:
            return max(1, (len(self._items) - 1) // max(1, self._visible_count) + 1)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.update_view()

    def _emit_pagination_changed(self) -> None:
        if self._pending_pagination_emit:
            return
        self._pending_pagination_emit = True
        QTimer.singleShot(0, self._emit_pagination_delayed)

    def _emit_pagination_delayed(self) -> None:
        self._pending_pagination_emit = False
        state = (self.get_current_page(), self.get_total_pages())
        if state != self._last_pagination_state:
            self._last_pagination_state = state
            self.pagination_changed.emit(*state)
