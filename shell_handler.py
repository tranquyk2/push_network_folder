import sys
import os
import ctypes
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path để import được các module
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load_config, APP_DIR
from file_utils import is_file_locked
from database import init_db, log_history
import shutil

# ── Progress popup (PyQt) ──
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

LOG_PATH = APP_DIR / "shell_handler.log"


class ProgressPopup(QWidget):

    def __init__(self, total_files: int, dest_name: str):
        super().__init__()
        self.setWindowTitle("NAS Uploader")
        self.setFixedSize(360, 110)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("""
            background: #1c1e2e;
            border: 1px solid #7c6cff;
            border-radius: 12px;
            color: #e4e6f0;
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(6)

        self.title_label = QLabel(f"Gửi lên {dest_name}")
        self.title_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #e4e6f0; border: none;"
        )
        layout.addWidget(self.title_label)

        self.file_label = QLabel("Đang chuẩn bị...")
        self.file_label.setStyleSheet(
            "font-size: 11px; color: #8b8ea8; border: none;"
        )
        layout.addWidget(self.file_label)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setMaximum(total_files)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #161822; border: 1px solid #2a2d42;
                border-radius: 6px; text-align: center;
                color: #e4e6f0; height: 16px; font-size: 10px;
            }
            QProgressBar::chunk {
                background: #7c6cff; border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress)

        self.setLayout(layout)
        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.geometry().center()
            self.move(center.x() - self.width() // 2,
                      center.y() - self.height() // 2 - 100)

    def update_progress(self, current: int, filename: str, status: str = ""):
        """Cập nhật tiến trình."""
        self.progress.setValue(current)
        short = filename if len(filename) < 40 else filename[:37] + "..."
        if status == "hash":
            self.file_label.setText(f"Đang kiểm tra: {short}")
        elif status == "copy":
            self.file_label.setText(f"Đang gửi: {short}")
        elif status == "skip":
            self.file_label.setText(f"Đã tồn tại: {short}")
        elif status == "done":
            self.file_label.setText(f"Hoàn tất: {short}")
        else:
            self.file_label.setText(short)
        QApplication.processEvents()

    def show_result(self, success: int, errors: int, skipped: int):
        """Hiển thị kết quả cuối cùng rồi tự đóng."""
        if errors == 0 and skipped == 0:
            msg = f"Đã gửi {success} file thành công"
            color = "#34d399"
        elif errors > 0:
            msg = f"{success} thành công, {errors} lỗi"
            color = "#f87171" if errors > 0 else "#fbbf24"
        else:
            msg = f"{success} thành công, {skipped} bỏ qua"
            color = "#fbbf24"

        self.file_label.setText(msg)
        self.file_label.setStyleSheet(
            f"font-size: 11px; color: {color}; font-weight: 600; border: none;"
        )
        self.progress.hide()
        self.title_label.setText("Hoàn tất")

        QTimer.singleShot(2500, self.close)


def _log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


def confirm_overwrite(filename: str, dest_path: str) -> bool:
    MB_YESNO = 0x04
    MB_ICONQUESTION = 0x20
    MB_TOPMOST = 0x40000
    MB_DEFBUTTON2 = 0x100  # Mặc định chọn No

    result = ctypes.windll.user32.MessageBoxW(
        0,
        f"File '{filename}' đã tồn tại tại đích.\n\n"
        f"{dest_path}\n\n"
        f"Bạn có muốn ghi đè không?",
        "NAS Uploader - Xác nhận ghi đè",
        MB_YESNO | MB_ICONQUESTION | MB_TOPMOST | MB_DEFBUTTON2,
    )
    return result == 6  # IDYES = 6


def show_toast(title: str, message: str, icon_type: str = "info"):
    _log(f"TOAST [{icon_type}] {title}: {message}")

    try:
        from winotify import Notification
        toast = Notification(
            app_id="Uploader",
            title=title,
            msg=message,
        )
        toast.show()
        return
    except Exception as e:
        _log(f"  winotify failed: {e}")

    # Fallback: MessageBox
    try:
        flags = {
            "info": 0x40,
            "warning": 0x30,
            "error": 0x10,
        }.get(icon_type, 0x40)
        ctypes.windll.user32.MessageBoxW(0, message, title, flags | 0x40000)
    except Exception as e:
        _log(f"  MessageBox failed: {e}")


def main():
    _log("=" * 50)
    _log(f"shell_handler started, args: {sys.argv}")

    try:
        init_db()

        # ── Parse arguments: chỉ lấy file paths sau --dest <name> ──
        dest_name = ""
        file_paths = []

        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == "--dest" and i + 1 < len(sys.argv):
                dest_name = sys.argv[i + 1]
                file_paths = sys.argv[i + 2:]  # mọi thứ sau --dest <name> là file
                break
            i += 1

        if not dest_name or not file_paths:
            show_toast("Uploader", "Dùng: --dest <tên_đích> <file1> [file2...]", "warning")
            sys.exit(1)

        _log(f"dest_name={dest_name}, file_paths={file_paths}")

        # ── Load config & xác minh đích ──
        cfg = load_config()
        dest_folder = cfg.get("destinations", {}).get(dest_name, "")
        _log(f"dest_folder={dest_folder}")

        if not dest_folder:
            show_toast("Uploader", f"Không tìm thấy đích '{dest_name}'.", "error")
            sys.exit(1)

        if not os.path.isdir(dest_folder):
            show_toast(
                "Uploader",
                f"Không kết nối được tới '{dest_name}' ({dest_folder}).\nKiểm tra VPN/mạng.",
                "error",
            )
            sys.exit(1)

        # ── Khởi tạo progress popup ──
        qt_app = QApplication(sys.argv)
        popup = ProgressPopup(len(file_paths), dest_name)
        popup.show()
        QApplication.processEvents()

        # ── Copy từng file ──
        success = 0
        errors = 0
        skipped = 0

        for idx, src in enumerate(file_paths, start=1):
            if not os.path.isfile(src):
                _log(f"SKIP not a file: {src}")
                errors += 1
                popup.update_progress(idx, os.path.basename(src), "error")
                continue

            filename = os.path.basename(src)
            dest_path = os.path.join(dest_folder, filename)
            _log(f"Processing: {src} -> {dest_path}")

            # Hiển thị popup ngay — trước mọi thao tác nặng
            popup.update_progress(idx - 1, filename, "copy")

            # Kiểm tra file đích bị khóa
            if is_file_locked(dest_path):
                _log(f"LOCKED: {dest_path}")
                log_history(filename, src, dest_path, "error", "File đích bị khóa")
                errors += 1
                popup.update_progress(idx, filename, "error")
                continue

            # Kiểm tra trùng tên → hỏi ghi đè
            if os.path.exists(dest_path):
                if not confirm_overwrite(filename, dest_path):
                    _log(f"SKIP user declined: {filename}")
                    log_history(filename, src, dest_path, "skip",
                                "Người dùng từ chối ghi đè")
                    skipped += 1
                    popup.update_progress(idx, filename, "skip")
                    continue
                _log(f"OVERWRITE: {filename}")

            # Copy
            try:
                shutil.copy2(src, dest_path)
                log_history(filename, src, dest_path, "success", "Đã copy")
                success += 1
                _log(f"OK: {filename}")
                popup.update_progress(idx, filename, "done")
            except Exception as e:
                log_history(filename, src, dest_path, "error", str(e))
                errors += 1
                _log(f"COPY ERROR: {filename} - {e}")
                popup.update_progress(idx, filename, "error")

        # ── hisn thị kết quả ──
        popup.show_result(success, errors, skipped)
        qt_app.exec()  # giữ popup hiển thị 2.5s rồi tự đóng

    except Exception as e:
        _log(f"FATAL ERROR: {e}")
        _log(traceback.format_exc())
        show_toast("Uploader", f"Lỗi: {e}", "error")


if __name__ == "__main__":
    main()

