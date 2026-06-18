from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .. import events


def is_real_prompt(rec: dict) -> bool:
    if rec.get("type") != "user":
        return False
    if rec.get("isMeta") or rec.get("isSidechain"):
        return False
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return False
    content = msg.get("content")
    if not isinstance(content, str):
        return False
    if content.startswith("<local-command") or content.startswith("<command-"):
        return False
    return True


def _minutes(first: str, last: str) -> int:
    if not first or not last:
        return 0
    delta = events.parse_ts(last) - events.parse_ts(first)
    return int(delta.total_seconds() // 60)


def parse_claude_session(path, session_id: str | None = None) -> events.ParseResult:
    sid = session_id or Path(path).stem
    days: dict = {}
    session_ai_title = None
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

            if rec.get("type") == "ai-title" and rec.get("aiTitle"):
                session_ai_title = rec["aiTitle"]
                continue

            ts = rec.get("timestamp")
            if not ts:
                continue
            day = events.to_local_date(ts)
            d = days.get(day)
            if d is None:
                d = {"first_ts": ts, "last_ts": ts, "prompt_count": 0,
                     "tools": Counter(), "models": [], "cwd": None,
                     "branch": None, "summary": None}
                days[day] = d

            if events.parse_ts(ts) < events.parse_ts(d["first_ts"]):
                d["first_ts"] = ts
            if events.parse_ts(ts) > events.parse_ts(d["last_ts"]):
                d["last_ts"] = ts
            if rec.get("cwd"):
                d["cwd"] = rec["cwd"]
            if rec.get("gitBranch"):
                d["branch"] = rec["gitBranch"]

            if is_real_prompt(rec):
                d["prompt_count"] += 1
                if d["summary"] is None:
                    d["summary"] = rec["message"]["content"][:200]

            if rec.get("type") == "assistant":
                msg = rec.get("message")
                if isinstance(msg, dict):
                    model = msg.get("model")
                    if model and model not in d["models"]:
                        d["models"].append(model)
                    for b in msg.get("content", []) or []:
                        if isinstance(b, dict) and b.get("type") == "tool_use":
                            d["tools"][b.get("name", "?")] += 1

    out = []
    for day, d in sorted(days.items()):
        title = session_ai_title or d["summary"] or "(untitled session)"
        out.append({
            "schema_version": events.SCHEMA_VERSION,
            "event_id": events.make_session_event_id("claude", sid, day),
            "ts": d["last_ts"], "date": day, "tool": "claude", "kind": "session_day",
            "project": events.derive_project(d["cwd"]) if d["cwd"] else None,
            "cwd": d["cwd"], "git_branch": d["branch"], "session_id": sid,
            "title": title, "summary": d["summary"] or "",
            "meta": {
                "prompt_count": d["prompt_count"],
                "tool_use_count": sum(d["tools"].values()),
                "tool_breakdown": dict(d["tools"]),
                "duration_min": _minutes(d["first_ts"], d["last_ts"]),
                "first_ts": d["first_ts"], "last_ts": d["last_ts"],
                "model": d["models"][-1] if d["models"] else None,
                "models": sorted(d["models"]),
            },
            "raw_ref": f"archive/claude/{sid}.jsonl",
        })
    return events.ParseResult(out, skipped)
