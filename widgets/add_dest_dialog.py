"""
Dialog thêm đích mới (tên hiển thị + đường dẫn) — thiết kế hiện đại.
"""

from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt


class AddDestinationDialog(QDialog):
    """Dialog nhập tên hiển thị và đường dẫn thư mục đích."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm đích mới")
        self.setMinimumWidth(460)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Thêm đích lưu mới")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        desc = QLabel("Nhập tên hiển thị của thư mục và đường dẫn thư mục đích để lưu file.")
        desc.setObjectName("headerSubtitle")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setObjectName("divider")
        layout.addWidget(divider)

        # Name field
        name_label = QLabel("Tên hiển thị")
        name_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ví dụ: Production, Backup, etc.")
        self.name_input.setMinimumHeight(36)
        layout.addWidget(self.name_input)

        # Path field
        path_label = QLabel("Đường dẫn thư mục")
        path_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(
            r"Ví dụ: Z:\Production hoặc \\server\share\Production"
        )
        self.path_input.setMinimumHeight(36)
        browse_btn = QPushButton("📁 Chọn...")
        browse_btn.setObjectName("toolbarBtn")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setMinimumHeight(36)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self.path_input)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        layout.addSpacing(8)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Hủy")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Thêm đích")
        ok_btn.setObjectName("primaryBtn")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setMinimumHeight(36)
        ok_btn.setMinimumWidth(110)
        ok_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục đích")
        if folder:
            self.path_input.setText(folder)

    def get_values(self) -> tuple:
        """Trả về (tên, đường_dẫn) đã nhập."""
        return self.name_input.text().strip(), self.path_input.text().strip()
