"""
Shell handler — Được gọi từ Windows context menu khi người dùng
click phải file → "Gửi lên NAS → Tên đích".

Cách dùng:
    pythonw shell_handler.py --dest "EQM" "C:/path/to/file1.txt"
"""

import sys
import os
import ctypes
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path để import được các module
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load_config, APP_DIR
from file_utils import file_hash, is_file_locked
from database import init_db, log_history
import shutil

LOG_PATH = APP_DIR / "shell_handler.log"


def _log(msg: str):
    """Ghi log ra file (vì pythonw.exe không có console)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


def confirm_overwrite(filename: str, dest_path: str) -> bool:
    """Hiện MessageBox hỏi người dùng có muốn ghi đè file đích không."""
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
    """Hiển thị Windows toast notification hoặc fallback MessageBox."""
    _log(f"TOAST [{icon_type}] {title}: {message}")

    try:
        from winotify import Notification
        toast = Notification(
            app_id="NAS Uploader",
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

        # ── Parse arguments ──
        args = sys.argv[1:]
        if len(args) < 3 or args[0] != "--dest":
            show_toast("NAS Uploader", "Dùng: --dest <tên_đích> <file1> [file2...]", "warning")
            sys.exit(1)

        dest_name = args[1]
        file_paths = args[2:]
        _log(f"dest_name={dest_name}, file_paths={file_paths}")

        # ── Load config & xác minh đích ──
        cfg = load_config()
        dest_folder = cfg.get("destinations", {}).get(dest_name, "")
        _log(f"dest_folder={dest_folder}")

        if not dest_folder:
            show_toast("NAS Uploader", f"Không tìm thấy đích '{dest_name}'.", "error")
            sys.exit(1)

        if not os.path.isdir(dest_folder):
            show_toast(
                "NAS Uploader",
                f"Không kết nối được tới '{dest_name}' ({dest_folder}).\nKiểm tra VPN/mạng.",
                "error",
            )
            sys.exit(1)

        # ── Copy từng file ──
        success = 0
        errors = 0
        skipped = 0

        for src in file_paths:
            if not os.path.isfile(src):
                _log(f"SKIP not a file: {src}")
                errors += 1
                continue

            filename = os.path.basename(src)
            dest_path = os.path.join(dest_folder, filename)
            _log(f"Processing: {src} -> {dest_path}")

            # Kiểm tra file đích bị khóa
            if is_file_locked(dest_path):
                _log(f"LOCKED: {dest_path}")
                log_history(filename, src, dest_path, "error", "File đích bị khóa")
                errors += 1
                continue

            # Kiểm tra trùng
            if os.path.exists(dest_path):
                if os.path.getsize(src) == os.path.getsize(dest_path) and \
                   file_hash(src) == file_hash(dest_path):
                    _log(f"SKIP identical: {filename}")
                    log_history(filename, src, dest_path, "skip", "Trùng nội dung")
                    skipped += 1
                    continue
                else:
                    # File khác nội dung → hỏi người dùng có ghi đè không
                    if not confirm_overwrite(filename, dest_path):
                        _log(f"SKIP user declined overwrite: {filename}")
                        log_history(filename, src, dest_path, "skip",
                                    "Người dùng từ chối ghi đè")
                        skipped += 1
                        continue
                    _log(f"OVERWRITE: {filename}")

            # Copy
            try:
                shutil.copy2(src, dest_path)
                if file_hash(src) == file_hash(dest_path):
                    log_history(filename, src, dest_path, "success", "Đã xác minh hash")
                    success += 1
                    _log(f"OK: {filename}")
                else:
                    log_history(filename, src, dest_path, "error", "Hash không khớp")
                    errors += 1
                    _log(f"HASH MISMATCH: {filename}")
            except Exception as e:
                log_history(filename, src, dest_path, "error", str(e))
                errors += 1
                _log(f"COPY ERROR: {filename} - {e}")

        # ── Thông báo kết quả ──
        parts = []
        if success:
            parts.append(f"{success} thành công")
        if skipped:
            parts.append(f"{skipped} bỏ qua")
        if errors:
            parts.append(f"{errors} lỗi")

        msg = f"Đã đẩy lên '{dest_name}': {', '.join(parts)}."
        _log(f"RESULT: {msg}")
        show_toast(
            "NAS Uploader",
            msg,
            "warning" if errors else "info",
        )

    except Exception as e:
        _log(f"FATAL ERROR: {e}")
        _log(traceback.format_exc())
        show_toast("NAS Uploader", f"Lỗi: {e}", "error")


if __name__ == "__main__":
    main()

