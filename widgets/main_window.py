
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QProgressBar, QListWidget, QListWidgetItem, QMessageBox,
    QSystemTrayIcon, QMenu, QTabWidget, QDialog, QFrame,
    QGraphicsDropShadowEffect, QApplication, QSizePolicy,
    QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QFont

from config import load_config, save_config
from database import get_recent_history
from themes import THEMES, build_stylesheet
from copy_worker import CopyWorker
from context_menu import register as register_context_menu
from widgets.drop_zone import DropZone
from widgets.add_dest_dialog import AddDestinationDialog
from widgets.flow_layout import FlowLayout

# Startup shortcut path
STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
STARTUP_SHORTCUT = STARTUP_DIR / "NAS Uploader.lnk"


# ────────────────────── Constants ──────────────────────

ICON_PATH = str(Path(__file__).resolve().parent.parent / "folder.ico")


# ────────────────────── Helpers ──────────────────────

def make_card(layout_type=QVBoxLayout):
    frame = QFrame()
    frame.setObjectName("card")
    inner_layout = layout_type()
    inner_layout.setContentsMargins(0, 0, 0, 0)
    inner_layout.setSpacing(0)
    frame.setLayout(inner_layout)

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(32)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(0, 0, 0, 45))
    frame.setGraphicsEffect(shadow)

    return frame, inner_layout


def make_divider():
    line = QFrame()
    line.setObjectName("divider")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line


def make_section_header(title_text: str, buttons: list = None):
    
    header = QFrame()
    header.setObjectName("sectionHeader")
    h_layout = QHBoxLayout()
    h_layout.setContentsMargins(16, 10, 12, 10)
    h_layout.setSpacing(8)
    header.setLayout(h_layout)

    title = QLabel(title_text)
    title.setObjectName("sectionTitle")
    h_layout.addWidget(title)
    h_layout.addStretch()

    if buttons:
        for btn in buttons:
            h_layout.addWidget(btn)

    return header, title


# ────────────────────── MainWindow ──────────────────────

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ổ chung Uploader")
        self.resize(680, 750)
        self.setMinimumSize(480, 500)
        self.cfg = load_config()
        self.worker = None
        self.active_dest_name = self.cfg.get("last_used", "")
        self.theme_name = self.cfg.get("theme", "dark")
        self.setWindowIcon(QIcon(ICON_PATH))
        self._build_ui()
        self._build_tray()
        self.apply_theme()
        self._sync_context_menu()

        # Kiểm tra kết nối định kỳ
        self.conn_timer = QTimer(self)
        self.conn_timer.timeout.connect(self.check_connection_silent)
        self.conn_timer.start(15000)
        self.check_connection_silent()

    # ==================== Theme ====================
    def apply_theme(self):
        t = THEMES[self.theme_name]
        self.setStyleSheet(build_stylesheet(t))
        self.theme_toggle_btn.setText("☀️" if self.theme_name == "dark" else "🌙")

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.cfg["theme"] = self.theme_name
        save_config(self.cfg)
        self.apply_theme()

    # ==================== Xây giao diện ====================
    def _build_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(12)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(10)


        self.theme_toggle_btn = QPushButton("🌙")
        self.theme_toggle_btn.setObjectName("iconBtn")
        self.theme_toggle_btn.setFixedSize(38, 38)
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_btn.setToolTip("Chuyển đổi giao diện sáng/tối")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        header.addWidget(self.theme_toggle_btn)
        outer.addLayout(header)

        # ── Connection Warning ──
        self.conn_status_label = QLabel("")
        self.conn_status_label.setObjectName("connWarning")
        self.conn_status_label.setWordWrap(True)
        self.conn_status_label.hide()
        outer.addWidget(self.conn_status_label)

        # ══════════════════════════════════════════════════
        # CARD 1: ĐÍCH LƯU FILE — với toolbar bên trên
        # ══════════════════════════════════════════════════
        dest_card, dest_card_layout = make_card()

        # Toolbar buttons
        add_btn = QPushButton("＋  Thêm đích")
        add_btn.setObjectName("toolbarBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Thêm đích lưu mới")
        add_btn.clicked.connect(self.add_destination)

        remove_btn = QPushButton("－  Xóa đích")
        remove_btn.setObjectName("toolbarBtn")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setToolTip("Xóa đích đang chọn")
        remove_btn.clicked.connect(self.remove_current_destination)

        open_folder_btn = QPushButton("📁  Mở thư mục")
        open_folder_btn.setObjectName("toolbarBtn")
        open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_folder_btn.setToolTip("Mở thư mục đích trong File Explorer")
        open_folder_btn.clicked.connect(self.open_current_destination)

        # Section header = title + toolbar buttons
        dest_header, _ = make_section_header(
            "ĐÍCH LƯU FILE",
            buttons=[add_btn, remove_btn, open_folder_btn]
        )
        dest_card_layout.addWidget(dest_header)
        dest_card_layout.addWidget(make_divider())

        # Destination chips area
        dest_body = QWidget()
        dest_body_layout = QVBoxLayout()
        dest_body_layout.setContentsMargins(16, 12, 16, 14)
        dest_body_layout.setSpacing(10)
        dest_body.setLayout(dest_body_layout)

        self.dest_buttons_row = FlowLayout(spacing_v=6)
        self.dest_buttons = {}
        self._rebuild_dest_buttons()
        dest_body_layout.addLayout(self.dest_buttons_row)

        # Active destination info
        self.current_dest_label = QLabel(self._current_dest_display())
        self.current_dest_label.setObjectName("destInfo")
        self.current_dest_label.setWordWrap(True)
        dest_body_layout.addWidget(self.current_dest_label)

        dest_card_layout.addWidget(dest_body)
        outer.addWidget(dest_card)

        # ══════════════════════════════════════════════════
        # CARD 2: KÉO-THẢ + TIẾN TRÌNH
        # ══════════════════════════════════════════════════
        drop_card, drop_card_layout = make_card()

        drop_header, _ = make_section_header("KÉO FILE VÀO ĐÂY")
        drop_card_layout.addWidget(drop_header)
        drop_card_layout.addWidget(make_divider())

        drop_body = QWidget()
        drop_body_layout = QVBoxLayout()
        drop_body_layout.setContentsMargins(16, 12, 16, 14)
        drop_body_layout.setSpacing(10)
        drop_body.setLayout(drop_body_layout)

        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.handle_files_dropped)
        drop_body_layout.addWidget(self.drop_zone)

        # Progress row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        progress_row.addWidget(self.progress_bar)
        drop_body_layout.addLayout(progress_row)

        self.status_label = QLabel("Sẵn sàng.")
        self.status_label.setObjectName("statusLabel")
        drop_body_layout.addWidget(self.status_label)

        drop_card_layout.addWidget(drop_body)
        outer.addWidget(drop_card)

        # ══════════════════════════════════════════════════
        # CARD 3: KẾT QUẢ / LỊCH SỬ
        # ══════════════════════════════════════════════════
        result_card, result_card_layout = make_card()

        result_header, _ = make_section_header("KẾT QUẢ & LỊCH SỬ")
        result_card_layout.addWidget(result_header)
        result_card_layout.addWidget(make_divider())

        result_body = QWidget()
        result_body_layout = QVBoxLayout()
        result_body_layout.setContentsMargins(12, 10, 12, 12)
        result_body_layout.setSpacing(0)
        result_body.setLayout(result_body_layout)

        self.tabs = QTabWidget()
        self.result_list = QListWidget()
        self.tabs.addTab(self.result_list, "Phiên này")
        self.history_list = QListWidget()
        self.tabs.addTab(self.history_list, "Lịch sử")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        result_body_layout.addWidget(self.tabs)

        result_card_layout.addWidget(result_body)
        outer.addWidget(result_card, stretch=1)

        self.setLayout(outer)

    # ==================== Quản lý đích ====================
    def _current_dest_display(self) -> str:
        path = self.cfg["destinations"].get(self.active_dest_name, "")
        if not path:
            return "Chưa chọn đích nào — bấm '＋ Thêm đích' ở thanh công cụ bên trên."
        return f"📍  {self.active_dest_name}  →  {path}"

    def _rebuild_dest_buttons(self):
        while self.dest_buttons_row.count():
            item = self.dest_buttons_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.dest_buttons = {}

        for name in self.cfg["destinations"]:
            btn = QPushButton(name)
            btn.setObjectName("destBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setChecked(name == self.active_dest_name)
            btn.clicked.connect(lambda checked, n=name: self.select_destination(n))
            self.dest_buttons_row.addWidget(btn)
            self.dest_buttons[name] = btn

        if not self.cfg["destinations"]:
            empty_label = QLabel(
                "Chưa có đích nào — bấm  ＋ Thêm đích  ở thanh công cụ"
            )
            empty_label.setObjectName("destInfo")
            empty_label.setStyleSheet("font-style: italic;")
            self.dest_buttons_row.addWidget(empty_label)

    def _sync_context_menu(self):
        
        register_context_menu(self.cfg.get("destinations", {}))

    def select_destination(self, name: str):
        self.active_dest_name = name
        self.cfg["last_used"] = name
        save_config(self.cfg)
        for n, btn in self.dest_buttons.items():
            btn.setChecked(n == name)
        self.current_dest_label.setText(self._current_dest_display())
        self.progress_bar.setValue(0)
        self.check_connection_silent()

    def add_destination(self):
        dialog = AddDestinationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, path = dialog.get_values()
            if not name or not path:
                QMessageBox.warning(self, "Thiếu thông tin",
                                    "Vui lòng nhập đủ tên và đường dẫn.")
                return
            self.cfg["destinations"][name] = path
            self.cfg["last_used"] = name
            self.active_dest_name = name
            save_config(self.cfg)
            self._rebuild_dest_buttons()
            self.current_dest_label.setText(self._current_dest_display())
            self.check_connection_silent()
            self._sync_context_menu()

    def remove_current_destination(self):
        if (not self.active_dest_name
                or self.active_dest_name not in self.cfg["destinations"]):
            QMessageBox.information(self, "Chưa chọn đích",
                                    "Chưa có đích nào đang được chọn để xóa.")
            return
        confirm = QMessageBox.question(
            self, "Xác nhận",
            f"Xóa đích '{self.active_dest_name}' khỏi danh sách? "
            "(Không xóa file, chỉ xóa lối tắt)"
        )
        if confirm == QMessageBox.StandardButton.Yes:
            del self.cfg["destinations"][self.active_dest_name]
            self.active_dest_name = next(iter(self.cfg["destinations"]), "")
            self.cfg["last_used"] = self.active_dest_name
            save_config(self.cfg)
            self._rebuild_dest_buttons()
            self.current_dest_label.setText(self._current_dest_display())
            self._sync_context_menu()

    def open_current_destination(self):
        path = self.cfg["destinations"].get(self.active_dest_name, "")
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Không mở được",
                                "Đích chưa hợp lệ hoặc chưa kết nối được.")
            return
        try:
            os.startfile(path)
        except AttributeError:
            QMessageBox.information(
                self, "Không hỗ trợ",
                "Chức năng mở thư mục chỉ hỗ trợ trên Windows."
            )

    # ==================== Kiểm tra kết nối ====================
    def check_connection_silent(self):
        
        path = self.cfg["destinations"].get(self.active_dest_name, "")
        if not path:
            self.conn_status_label.hide()
            return
        if os.path.isdir(path):
            self.conn_status_label.hide()
        else:
            self.conn_status_label.setText(
                f"Không kết nối được tới '{self.active_dest_name}' "
                f"({path}). Kiểm tra mạng hoặc đăng nhập lại qua File Explorer."
            )
            self.conn_status_label.show()

    # ==================== Xử lý kéo-thả ====================
    def handle_files_dropped(self, paths: list):
        dest = self.cfg["destinations"].get(self.active_dest_name, "")
        if not dest:
            QMessageBox.warning(
                self, "Thiếu đích",
                "Vui lòng chọn hoặc thêm một đích trước khi kéo file vào."
            )
            return
        if not os.path.isdir(dest):
            QMessageBox.critical(
                self, "Không kết nối được",
                f"Không truy cập được thư mục đích:\n{dest}\n\n"
                "Kiểm tra lại mạng, hoặc đăng nhập lại qua File Explorer trước."
            )
            return

        # Lọc file trùng — hỏi người dùng có ghi đè không
        approved = []

        for src in paths:
            filename = os.path.basename(src)
            dest_path = os.path.join(dest, filename)

            if os.path.exists(dest_path):
                btn = QMessageBox.question(
                    self, "File đã tồn tại",
                    f"'{filename}' đã tồn tại tại đích.\n\nBạn có muốn ghi đè?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if btn == QMessageBox.StandardButton.Yes:
                    approved.append(src)
                else:
                    item = QListWidgetItem(f"⏭ {filename} — Đã tồn tại, bỏ qua")
                    item.setForeground(Qt.GlobalColor.darkGray)
                    self.result_list.addItem(item)
            else:
                approved.append(src)

        if not approved:
            self.status_label.setText("Không có file nào để đẩy.")
            return

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(approved))
        self.status_label.setText(
            f"Đang đẩy {len(approved)} file vào '{self.active_dest_name}'..."
        )

        self.worker = CopyWorker(approved, dest)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.file_status.connect(self._on_file_status)
        self.worker.finished_all.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, done: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(done)

    def _on_file_status(self, filename: str, status: str, message: str):
        icon = {"success": "✅", "error": "❌", "skip": "⏭"}.get(status, "•")
        item = QListWidgetItem(f"{icon} {filename} — {message}")
        if status == "error":
            item.setForeground(Qt.GlobalColor.red)
        elif status == "skip":
            item.setForeground(Qt.GlobalColor.darkGray)
        self.result_list.addItem(item)
        self.result_list.scrollToBottom()

    def _on_finished(self, success_count: int, error_count: int):
        self.status_label.setText(
            f"Hoàn tất: {success_count} thành công, {error_count} lỗi."
        )
        if error_count > 0:
            self.tray_icon.showMessage(
                "Ổ chung Uploader",
                f"Hoàn tất với {error_count} lỗi - kiểm tra lại danh sách kết quả.",
                QSystemTrayIcon.MessageIcon.Warning, 5000
            )
        else:
            self.tray_icon.showMessage(
                "Ổ chung Uploader",
                f"Đã đẩy xong {success_count} file thành công.",
                QSystemTrayIcon.MessageIcon.Information, 3000
            )

    # ==================== Tab lịch sử ====================
    def on_tab_changed(self, index: int):
        if self.tabs.tabText(index).strip().endswith("Lịch sử"):
            self._load_history_tab()

    def _load_history_tab(self):
        self.history_list.clear()
        rows = get_recent_history(200)
        icon_map = {"success": "✅", "error": "❌", "skip": "⏭"}
        for filename, dest_path, status, message, ts in rows:
            icon = icon_map.get(status, "•")
            item = QListWidgetItem(
                f"{icon} [{ts}] {filename} → {dest_path} ({message})"
            )
            if status == "error":
                item.setForeground(Qt.GlobalColor.red)
            self.history_list.addItem(item)

    # ==================== Khay hệ thống ====================
    def _build_tray(self):
        icon = QIcon(ICON_PATH)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Uploader")

        menu = QMenu()
        show_action = QAction("Mở Uploader", self)
        show_action.triggered.connect(self.showNormal)

        self.startup_action = QAction("Khởi động cùng Windows", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self._is_startup_enabled())
        self.startup_action.triggered.connect(self._toggle_startup)

        quit_action = QAction("Thoát", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(self.startup_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    # ==================== Auto-start với Windows ====================
    def _is_startup_enabled(self) -> bool:
        return STARTUP_SHORTCUT.exists()

    def _toggle_startup(self, enabled: bool):
        if enabled:
            self._create_startup_shortcut()
        else:
            self._remove_startup_shortcut()
        self.startup_action.setChecked(self._is_startup_enabled())

    def _create_startup_shortcut(self):
        
        try:
            import pythoncom
            from win32comext.shell import shell, shellcon

            STARTUP_DIR.mkdir(parents=True, exist_ok=True)
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None,
                pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLinkW
            )
            shortcut.SetPath(sys.executable)
            shortcut.SetArguments(
                f'"{Path(__file__).resolve().parent.parent / "main.py"}"'
            )
            shortcut.SetWorkingDirectory(
                str(Path(__file__).resolve().parent.parent)
            )
            shortcut.SetDescription("NAS Uploader")
            shortcut.SetIconLocation(ICON_PATH, 0)

            persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist.Save(str(STARTUP_SHORTCUT), 0)
        except ImportError:
            self._create_startup_shortcut_fallback()

    def _create_startup_shortcut_fallback(self):
        """Fallback: dùng PowerShell tạo shortcut nếu không có pywin32."""
        import subprocess
        STARTUP_DIR.mkdir(parents=True, exist_ok=True)
        ps = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{STARTUP_SHORTCUT}")
$sc.TargetPath = "{sys.executable.replace('python.exe', 'pythonw.exe')}"
$sc.Arguments = '"{Path(__file__).resolve().parent.parent / "main.py"}"'
$sc.WorkingDirectory = "{Path(__file__).resolve().parent.parent}"
$sc.IconLocation = "{ICON_PATH}"
$sc.Save()
'''
        subprocess.run(["powershell", "-Command", ps],
                       capture_output=True, creationflags=0x08000000)

    def _remove_startup_shortcut(self):
        try:
            STARTUP_SHORTCUT.unlink()
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Uploader vẫn đang chạy",
            "App đã thu nhỏ xuống khay hệ thống. "
            "Bấm icon để mở lại, hoặc chọn Thoát để đóng hẳn.",
            QSystemTrayIcon.MessageIcon.Information, 3000
        )
