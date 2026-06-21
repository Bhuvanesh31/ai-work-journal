from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

from . import events

COLUMNS = ["event_id", "ts", "date", "tool", "kind", "project", "cwd",
           "git_branch", "session_id", "title", "summary", "meta", "raw_ref"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id   TEXT PRIMARY KEY,
    ts         TEXT,
    date       TEXT,
    tool       TEXT,
    kind       TEXT,
    project    TEXT,
    cwd        TEXT,
    git_branch TEXT,
    session_id TEXT,
    title      TEXT,
    summary    TEXT,
    meta       TEXT,
    raw_ref    TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
"""


def connect(paths) -> sqlite3.Connection:
    paths.root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(paths.db))
    conn.executescript(_SCHEMA)
    return conn


def _row_from_event(e: dict):
    return (e["event_id"], e["ts"], e["date"], e["tool"], e["kind"],
            e.get("project"), e.get("cwd"), e.get("git_branch"),
            e.get("session_id"), e.get("title"), e.get("summary"),
            json.dumps(e.get("meta", {}), ensure_ascii=False), e.get("raw_ref"))


def _event_from_row(r) -> dict:
    d = dict(zip(COLUMNS, r))
    d["meta"] = json.loads(d["meta"]) if d["meta"] else {}
    d["schema_version"] = events.SCHEMA_VERSION
    return d


def existing_event_ids(conn) -> set:
    return {row[0] for row in conn.execute("SELECT event_id FROM events")}


def _insert(conn, e: dict) -> None:
    placeholders = ",".join(["?"] * len(COLUMNS))
    conn.execute(f"INSERT OR IGNORE INTO events ({','.join(COLUMNS)}) "
                 f"VALUES ({placeholders})", _row_from_event(e))


def append_events(paths, conn, evs) -> int:
    have = existing_event_ids(conn)
    added = 0
    with open(paths.events, "a", encoding="utf-8") as f:
        for e in evs:
            if e["event_id"] in have:
                continue
            have.add(e["event_id"])
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
            _insert(conn, e)
            added += 1
    conn.commit()
    return added


def archive_file(paths, tool: str, src_path) -> Path:
    dest_dir = paths.claude_archive if tool == "claude" else paths.codex_archive
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / Path(src_path).name
    shutil.copy2(str(src_path), str(dest))
    return dest


def rebuild(paths) -> int:
    if paths.db.exists():
        paths.db.unlink()
    conn = connect(paths)
    n = 0
    if paths.events.exists():
        with open(paths.events, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                _insert(conn, json.loads(line))
                n += 1
    conn.commit()
    conn.close()
    return n


def query_range(conn, start_date: str, end_date: str):
    cur = conn.execute(
        f"SELECT {','.join(COLUMNS)} FROM events "
        "WHERE date BETWEEN ? AND ? ORDER BY date, ts",
        (start_date, end_date))
    return [_event_from_row(r) for r in cur.fetchall()]


def distinct_cwds(conn):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT cwd FROM events WHERE cwd IS NOT NULL")]


def counts(conn) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    by_tool = {row[0]: row[1] for row in conn.execute(
        "SELECT tool, COUNT(*) FROM events GROUP BY tool")}
    return {"total": total, "by_tool": by_tool}
