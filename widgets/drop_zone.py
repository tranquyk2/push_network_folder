"""
Vùng kéo-thả file (DropZone widget) — thiết kế hiện đại.
"""

import os

from PyQt6.QtWidgets import QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal


class DropZone(QLabel):
    """QLabel hỗ trợ kéo-thả file/thư mục, hoặc click để chọn file."""

    files_dropped = pyqtSignal(list)

    IDLE_TEXT = (
        "📂\n\n"
        "Kéo file hoặc thư mục vào đây\n"
        "hoặc bấm để chọn file"
    )
    ACTIVE_TEXT = (
        "✨\n\n"
        "Thả file vào đây!"
    )

    def __init__(self):
        super().__init__(self.IDLE_TEXT)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

    def _reapply_style(self):
        """Buộc Qt re-polish widget để cập nhật stylesheet động."""
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setObjectName("dropZoneActive")
            self.setText(self.ACTIVE_TEXT)
            self._reapply_style()
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setObjectName("dropZone")
        self.setText(self.IDLE_TEXT)
        self._reapply_style()

    def mousePressEvent(self, event):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn file để đẩy lên")
        if files:
            self.files_dropped.emit(files)

    def dropEvent(self, event):
        self.setObjectName("dropZone")
        self.setText(self.IDLE_TEXT)
        self._reapply_style()
        paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if os.path.isdir(local_path):
                for root, _, files in os.walk(local_path):
                    for f in files:
                        paths.append(os.path.join(root, f))
            elif os.path.isfile(local_path):
                paths.append(local_path)
        if paths:
            self.files_dropped.emit(paths)
