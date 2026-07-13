"""
Các tiện ích thao tác file: hash SHA-256, kiểm tra file bị khóa.
"""

import hashlib
import os


def file_hash(path: str, block_size: int = 65536) -> str:
    """Tính hash SHA-256 của file để kiểm tra trùng lặp / xác minh toàn vẹn."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def is_file_locked(path: str) -> bool:
    """Kiểm tra xem file đích có đang bị khóa (đang mở bởi chương trình khác) không.
    Cách làm: thử mở file ở chế độ append độc quyền; nếu Windows chặn -> đang bị khóa."""
    if not os.path.exists(path):
        return False
    try:
        with open(path, "a"):
            pass
        return False
    except PermissionError:
        return True
    except Exception:
        return False
