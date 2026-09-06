"""
JETBOX — Kalıcı geçmiş (SQLite)

Render ve upload sonuçları jetbox.db'ye yazılır; Flask yeniden başlasa da
hangi beat'in yüklendiği bilinir (mükerrer upload engeli + History ekranı).
"""

import json
import os
import sqlite3
import threading
from datetime import datetime

_DB_PATH = None
_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL,            -- render | upload | schedule
    beat_filename TEXT,
    beat_name     TEXT,
    title         TEXT,
    video_id      TEXT,
    video_url     TEXT,
    privacy       TEXT,
    scheduled_at  TEXT,
    output_path   TEXT,
    status        TEXT NOT NULL,            -- done | failed
    error         TEXT,
    extra         TEXT,                     -- JSON
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_beat ON history(beat_filename);
CREATE INDEX IF NOT EXISTS idx_history_kind ON history(kind);
"""


def init_db(project_dir: str, filename: str = "jetbox.db") -> str:
    global _DB_PATH
    _DB_PATH = os.path.join(project_dir, filename)
    with _connect() as con:
        con.executescript(_SCHEMA)
    return _DB_PATH


def _connect():
    if not _DB_PATH:
        raise RuntimeError("history.init_db() çağrılmadı")
    con = sqlite3.connect(_DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def add_entry(kind: str, status: str = "done", **fields) -> int:
    cols = {
        "kind": kind, "status": status,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    for k in ("beat_filename", "beat_name", "title", "video_id", "video_url",
              "privacy", "scheduled_at", "output_path", "error"):
        if fields.get(k) is not None:
            cols[k] = fields[k]
    extra = {k: v for k, v in fields.items() if k not in cols and k != "extra"}
    if fields.get("extra"):
        extra.update(fields["extra"])
    if extra:
        cols["extra"] = json.dumps(extra, ensure_ascii=False, default=str)
    keys = ", ".join(cols)
    marks = ", ".join("?" for _ in cols)
    with _lock, _connect() as con:
        cur = con.execute(f"INSERT INTO history ({keys}) VALUES ({marks})", list(cols.values()))
        return cur.lastrowid


def list_entries(limit: int = 100, kind: str = None) -> list:
    q = "SELECT * FROM history"
    args = []
    if kind:
        q += " WHERE kind = ?"
        args.append(kind)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(int(limit))
    with _connect() as con:
        rows = con.execute(q, args).fetchall()
    return [_row(r) for r in rows]


def uploads_for_beat(beat_filename: str) -> list:
    """Bu dosya adıyla daha önce yapılmış başarılı upload/schedule kayıtları."""
    if not beat_filename:
        return []
    with _connect() as con:
        rows = con.execute(
            "SELECT * FROM history WHERE beat_filename = ? AND kind IN ('upload','schedule') "
            "AND status = 'done' ORDER BY id DESC", (beat_filename,)
        ).fetchall()
    return [_row(r) for r in rows]


def stats() -> dict:
    with _connect() as con:
        r = con.execute(
            "SELECT "
            " SUM(kind='render' AND status='done')  AS renders,"
            " SUM(kind IN ('upload','schedule') AND status='done') AS uploads,"
            " SUM(status='failed') AS failed,"
            " SUM(kind IN ('upload','schedule') AND status='done' AND date(created_at)=date('now','localtime')) AS uploads_today"
            " FROM history"
        ).fetchone()
    return {k: int(r[k] or 0) for k in r.keys()}


def _row(r) -> dict:
    d = dict(r)
    if d.get("extra"):
        try:
            d["extra"] = json.loads(d["extra"])
        except Exception:
            pass
    return d
