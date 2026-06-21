from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple

SCHEMA_VERSION = 1


class ParseResult(NamedTuple):
    events: List[Dict[str, Any]]
    skipped: int


def make_session_event_id(tool: str, session_id: str, date: str) -> str:
    return hashlib.sha1(f"{tool}|{session_id}|{date}".encode("utf-8")).hexdigest()


def make_commit_event_id(repo_path: str, commit_hash: str) -> str:
    return hashlib.sha1(f"git|{repo_path}|{commit_hash}".encode("utf-8")).hexdigest()


def derive_project(cwd: str) -> str:
    base = os.path.basename(cwd.rstrip("/")) or cwd
    return base.replace("_", "-").replace(" ", "-").lower()


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def to_local_date(ts: str) -> str:
    dt = parse_ts(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().strftime("%Y-%m-%d")
