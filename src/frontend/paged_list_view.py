from threading import Lock

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QScrollArea


class PagedListView(QWidget):
    """Виртуализированный список: переиспользует небольшой пул виджетов-строк и
    рендерит одну «страницу» строк по высоте вьюпорта. Виджет-строка должен иметь
    метод set_data(data). Перенесён из референса Encryption_app (PyQt5 -> PySide6)."""

    page_changed: Signal = Signal()
    pagination_changed: Signal = Signal(int, int)

    def __init__(self, item_widget_class, parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._lock = Lock()
        self._item_widget_class = item_widget_class

        self._items: dict = {}
        self._keys: list = []
        self._item_widgets: list[QWidget] = []

        self._first_visible_index = 0
        self._visible_count = 0
        self._last_pagination_state = (-1, -1)
        self._pending_pagination_emit = False

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._layout.addWidget(self._scroll_area)

        self._container = QWidget(self)
        self._container.setObjectName('w_view')
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setSpacing(8)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll_area.setWidget(self._container)

    @property
    def items_dict(self) -> dict:
        with self._lock:
            return self._items

    def set_items(self, items: dict):
        with self._lock:
            self._items = items
            self._keys = list(items.keys())
            self._first_visible_index = 0
        self.update_view()

    def resizeEvent(self, event):
        self.update_view()
        return super().resizeEvent(event)

    def update_view(self):
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

    def _update_widgets(self):
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

    def add_item(self, key, data):
        with self._lock:
            if key not in self._items:
                self._items[key] = data
                self._keys.insert(0, key)
        self.update_view()

    def update_item(self, key, data=None):
        """Обновить данные строки (если она видима — перерисовать)."""
        with self._lock:
            if key not in self._items:
                return
            if data is not None:
                self._items[key] = data
        self._update_widgets()

    def remove_item(self, key) -> bool:
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

    def clear_items(self):
        with self._lock:
            self._items.clear()
            self._keys.clear()
            self._first_visible_index = 0
        self._update_widgets()

    def get_total_items(self) -> int:
        with self._lock:
            return len(self._items)

    def set_page(self, page_number):
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

    def showEvent(self, event):
        super().showEvent(event)
        self.update_view()

    def _emit_pagination_changed(self):
        if self._pending_pagination_emit:
            return
        self._pending_pagination_emit = True
        QTimer.singleShot(0, self._emit_pagination_delayed)

    def _emit_pagination_delayed(self):
        self._pending_pagination_emit = False
        state = (self.get_current_page(), self.get_total_pages())
        if state != self._last_pagination_state:
            self._last_pagination_state = state
            self.pagination_changed.emit(*state)
