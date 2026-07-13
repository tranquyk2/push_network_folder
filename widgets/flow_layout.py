"""
Flow Layout — tự động wrap widget xuống dòng khi container hẹp lại.
Adapted from Qt's official FlowLayout example.
"""

from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtWidgets import QLayout, QSizePolicy, QStyle


class FlowLayout(QLayout):
    """Layout xếp widget theo dòng, tự động wrap khi hết chiều ngang."""

    def __init__(self, parent=None, margin=0, spacing_h=-1, spacing_v=-1):
        super().__init__(parent)
        self._items = []
        self._h_spacing = spacing_h
        self._v_spacing = spacing_v
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        """Xóa toàn bộ item khi layout bị hủy."""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    # ── spacing helpers ──
    def _horizontal_spacing(self) -> int:
        if self._h_spacing >= 0:
            return self._h_spacing
        # fontMetrics() belongs to QWidget, not QLayout — get from parent
        parent = self.parentWidget()
        if parent:
            return parent.fontMetrics().horizontalAdvance("x")
        return 10  # fallback

    def _vertical_spacing(self) -> int:
        if self._v_spacing >= 0:
            return self._v_spacing
        parent = self.parentWidget()
        if parent:
            return parent.fontMetrics().lineSpacing()
        return 16  # fallback

    # ── QLayout interface ──
    def addItem(self, item):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize(0, 0)
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                      margins.top() + margins.bottom())
        return size

    # ── Core layout logic ──
    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """Xếp widget theo dòng. Trả về chiều cao cần thiết."""
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(
            margins.left(), margins.top(),
            -margins.right(), -margins.bottom()
        )
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        h_spacing = self._horizontal_spacing()
        v_spacing = self._vertical_spacing()

        for item in self._items:
            widget = item.widget()
            space_x = h_spacing
            space_y = v_spacing

            if widget:
                size_hint = widget.sizeHint()
            else:
                size_hint = item.sizeHint()

            next_x = x + size_hint.width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                # Wrap sang dòng mới
                x = effective_rect.x()
                y += line_height + space_y
                next_x = x + size_hint.width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), size_hint))

            x = next_x
            line_height = max(line_height, size_hint.height())

        return y + line_height - rect.y() + margins.bottom()
