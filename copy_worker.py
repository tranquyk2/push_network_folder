import os
import shutil

from PyQt6.QtCore import QThread, pyqtSignal

from file_utils import is_file_locked
from database import log_history


class CopyWorker(QThread):

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

            # Kiểm tra file đích bị khóa
            if is_file_locked(dest_path):
                msg = "File đích đang bị khóa (có thể đang mở bởi người khác) - đã bỏ qua"
                self.file_status.emit(filename, "error", msg)
                log_history(filename, src, dest_path, "error", msg)
                error_count += 1
                self.progress_updated.emit(idx, total)
                continue

            # Copy
            try:
                shutil.copy2(src, dest_path)
                self.file_status.emit(filename, "success", f"Đã đẩy tới {dest_path}")
                log_history(filename, src, dest_path, "success", "OK")
                success_count += 1
            except Exception as e:
                error_count += 1
                err_msg = str(e)
                self.file_status.emit(filename, "error", err_msg)
                log_history(filename, src, dest_path, "error", err_msg)

            self.progress_updated.emit(idx, total)

        self.finished_all.emit(success_count, error_count)
