"""
Quản lý cấu hình ứng dụng: load/save config.json
"""

import json
from pathlib import Path

APP_DIR = Path.home() / ".nas_uploader"
APP_DIR.mkdir(exist_ok=True)
CONFIG_PATH = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "destinations": {},   # {"Tên hiển thị": "đường dẫn"}
    "last_used": "",
    "theme": "dark"
}


def load_config() -> dict:
    """Đọc cấu hình từ file JSON, trả về dict. Nếu lỗi hoặc file không tồn tại thì trả về mặc định."""
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # Tương thích ngược với bản cũ chỉ có "dest_folder"
            if "dest_folder" in cfg and "destinations" not in cfg:
                cfg = {
                    "destinations": {"Mặc định": cfg["dest_folder"]},
                    "last_used": "Mặc định"
                }
            cfg.setdefault("destinations", {})
            cfg.setdefault("last_used", "")
            cfg.setdefault("theme", "dark")
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """Ghi cấu hình ra file JSON."""
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
