"""
Luồng xử lý copy file (chạy nền QThread, không đơ giao diện).
"""

import os
import shutil

from PyQt6.QtCore import QThread, pyqtSignal

from file_utils import file_hash, is_file_locked
from database import log_history


class CopyWorker(QThread):
    """Luồng nền thực hiện copy file với: kiểm tra khóa file, trùng hash, retry, xác minh toàn vẹn."""

    progress_updated = pyqtSignal(int, int)       # (done, total)
    file_status = pyqtSignal(str, str, str)        # (filename, status, message)
    finished_all = pyqtSignal(int, int)            # (success_count, error_count)

    def __init__(self, file_paths: list, dest_folder: str, max_retries: int = 2):
        super().__init__()
        self.file_paths = file_paths
        self.dest_folder = dest_folder
        self.max_retries = max_retries

    def run(self):
        success_count = 0
        error_count = 0
        total = len(self.file_paths)

        for idx, src in enumerate(self.file_paths, start=1):
            filename = os.path.basename(src)
            dest_path = os.path.join(self.dest_folder, filename)

            try:
                # Cảnh báo nếu file đích đang bị khóa (đang mở bởi người khác)
                if is_file_locked(dest_path):
                    msg = "File đích đang bị khóa (có thể đang mở bởi người khác) - đã bỏ qua"
                    self.file_status.emit(filename, "error", msg)
                    log_history(filename, src, dest_path, "error", msg)
                    error_count += 1
                    self.progress_updated.emit(idx, total)
                    continue

                # Kiểm tra trùng file theo nội dung (hash)
                if os.path.exists(dest_path):
                    if os.path.getsize(src) == os.path.getsize(dest_path) and \
                       file_hash(src) == file_hash(dest_path):
                        self.file_status.emit(filename, "skip", "File giống hệt đã tồn tại, bỏ qua")
                        log_history(filename, src, dest_path, "skip", "Trùng nội dung")
                        success_count += 1
                        self.progress_updated.emit(idx, total)
                        continue
                    else:
                        # Tự động đổi tên nếu file khác nội dung
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        new_dest = os.path.join(self.dest_folder, f"{base}_{counter}{ext}")
                        while os.path.exists(new_dest):
                            counter += 1
                            new_dest = os.path.join(self.dest_folder, f"{base}_{counter}{ext}")
                        dest_path = new_dest

                # Copy với retry
                last_error = None
                for attempt in range(self.max_retries + 1):
                    try:
                        shutil.copy2(src, dest_path)
                        last_error = None
                        break
                    except Exception as e:
                        last_error = e

                if last_error is not None:
                    raise last_error

                # Xác minh toàn vẹn sau khi copy
                if file_hash(src) != file_hash(dest_path):
                    msg = "Copy xong nhưng xác minh nội dung KHÔNG khớp - vui lòng thử lại"
                    self.file_status.emit(filename, "error", msg)
                    log_history(filename, src, dest_path, "error", msg)
                    error_count += 1
                    self.progress_updated.emit(idx, total)
                    continue

                self.file_status.emit(filename, "success",
                                      f"Đã xác minh, đẩy tới {dest_path}")
                log_history(filename, src, dest_path, "success", "Đã xác minh hash")
                success_count += 1

            except Exception as e:
                error_count += 1
                err_msg = str(e)
                self.file_status.emit(filename, "error", err_msg)
                log_history(filename, src, dest_path, "error", err_msg)

            self.progress_updated.emit(idx, total)

        self.finished_all.emit(success_count, error_count)
