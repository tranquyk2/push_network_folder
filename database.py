import sqlite3
from datetime import datetime
from pathlib import Path

APP_DIR = Path.home() / ".nas_uploader"
APP_DIR.mkdir(exist_ok=True)
DB_PATH = APP_DIR / "history.db"


def init_db() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            source_path TEXT,
            dest_path TEXT,
            status TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_history(filename: str, source_path: str, dest_path: str,
                status: str, message: str = "") -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO history (filename, source_path, dest_path, status, message, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (filename, source_path, dest_path, status, message,
         datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 100) -> list:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        "SELECT filename, dest_path, status, message, timestamp FROM history "
        "ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows
