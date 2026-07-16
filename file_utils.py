import hashlib
import os


def file_hash(path: str, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def is_file_locked(path: str) -> bool:
    
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
