"""
Ổ chung Uploader v2 - Phần mềm kéo-thả file lên ổ mạng nội bộ (NAS/Windows share)
Chạy: python main.py
Yêu cầu: pip install PyQt6

Cấu trúc dự án:
    main.py              - Entry point
    config.py            - Load/save config
    database.py          - SQLite history
    file_utils.py        - Hash & file lock utilities
    themes.py            - Color palettes & QSS stylesheet generator
    copy_worker.py       - Background QThread for copying files
    context_menu.py      - Windows Explorer context menu registration
    shell_handler.py     - CLI handler for context menu actions
    widgets/
        __init__.py      - Package exports
        flow_layout.py   - Auto-wrapping flow layout
        drop_zone.py     - Drag-and-drop zone widget
        add_dest_dialog.py - Add destination dialog
        main_window.py   - Main application window
"""

import sys
import atexit

from PyQt6.QtWidgets import QApplication

from database import init_db
from config import load_config
from context_menu import register as register_context_menu, unregister as unregister_context_menu
from widgets.main_window import MainWindow


def main():
    init_db()

    # Đăng ký context menu Windows Explorer
    cfg = load_config()
    register_context_menu(cfg.get("destinations", {}))
    atexit.register(unregister_context_menu)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # giữ app sống khi đóng cửa sổ (tray icon)

    # Set app-wide icon (taskbar, alt-tab, etc.)
    from pathlib import Path
    from PyQt6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "folder.ico")))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()