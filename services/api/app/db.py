import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path(os.environ.get("ACACIA_DB_PATH", "/data/progress.db"))


def init_db(path: Optional[Path] = None) -> None:
    global DB_PATH
    p = path or DB_PATH
    # If caller provided a path use it as the active DB for subsequent calls
    DB_PATH = p
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                url TEXT PRIMARY KEY,
                done INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                ts INTEGER
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def upsert_progress(url: str, done: bool, score: int, ts: int) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO progress (url, done, score, ts) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(url) DO UPDATE SET done=excluded.done, score=excluded.score, ts=excluded.ts",
            (url, 1 if done else 0, int(score), int(ts)),
        )
        conn.commit()
    finally:
        conn.close()


def get_progress(url: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute("SELECT url, done, score, ts FROM progress WHERE url = ?", (url,))
        row = cur.fetchone()
        if not row:
            return None
        return {"url": row[0], "done": bool(row[1]), "score": row[2], "ts": row[3]}
    finally:
        conn.close()


def list_progress() -> Dict[str, Dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute("SELECT url, done, score, ts FROM progress")
        rows = cur.fetchall()
        return {r[0]: {"done": bool(r[1]), "score": r[2], "ts": r[3]} for r in rows}
    finally:
        conn.close()
