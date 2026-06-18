from __future__ import annotations

import json
from pathlib import Path

from .. import events


def codex_sessions_dir() -> Path:
    return Path.home() / ".codex" / "sessions"


def find_codex_rollouts(base=None):
    base = Path(base) if base is not None else codex_sessions_dir()
    if not base.exists():
        return []
    return sorted(base.rglob("rollout-*.jsonl"))


def _session_id_from_name(path) -> str:
    stem = Path(path).stem  # rollout-abc
    return stem[len("rollout-"):] if stem.startswith("rollout-") else stem


def parse_codex_rollout(path, session_id: str | None = None) -> events.ParseResult:
    sid = session_id or _session_id_from_name(path)
    days: dict = {}
    skipped = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                skipped += 1
                continue
            ts = rec.get("timestamp") or rec.get("ts")
            if not ts:
                continue
            day = events.to_local_date(ts)
            d = days.setdefault(day, {"first_ts": ts, "last_ts": ts,
                                      "prompt_count": 0, "msg_count": 0,
                                      "cwd": None, "summary": None})
            if events.parse_ts(ts) < events.parse_ts(d["first_ts"]):
                d["first_ts"] = ts
            if events.parse_ts(ts) > events.parse_ts(d["last_ts"]):
                d["last_ts"] = ts
            if rec.get("cwd"):
                d["cwd"] = rec["cwd"]
            d["msg_count"] += 1
            if rec.get("role") == "user":
                d["prompt_count"] += 1
                content = rec.get("content")
                if d["summary"] is None and isinstance(content, str):
                    d["summary"] = content[:200]

    out = []
    for day, d in sorted(days.items()):
        out.append({
            "schema_version": events.SCHEMA_VERSION,
            "event_id": events.make_session_event_id("codex", sid, day),
            "ts": d["last_ts"], "date": day, "tool": "codex", "kind": "session_day",
            "project": events.derive_project(d["cwd"]) if d["cwd"] else None,
            "cwd": d["cwd"], "git_branch": None, "session_id": sid,
            "title": d["summary"] or "(codex session)", "summary": d["summary"] or "",
            "meta": {"prompt_count": d["prompt_count"], "msg_count": d["msg_count"],
                     "first_ts": d["first_ts"], "last_ts": d["last_ts"],
                     "best_effort": True},
            "raw_ref": f"archive/codex/{Path(path).name}",
        })
    return events.ParseResult(out, skipped)
