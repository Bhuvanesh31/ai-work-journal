from __future__ import annotations

import subprocess

from .. import events

GIT_FORMAT = "%H%x1f%an%x1f%aI%x1f%s"


def _git(repo_path, *args, timeout: int = 30):
    try:
        return subprocess.run(["git", "-C", str(repo_path), *args],
                              capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def repo_toplevel(path) -> str | None:
    out = _git(path, "rev-parse", "--show-toplevel")
    if out is None or out.returncode != 0:
        return None
    top = out.stdout.strip()
    return top or None


def parse_git_log(repo_path, since: str | None = None) -> events.ParseResult:
    args = ["log", "--no-merges", "--date=iso-strict", f"--pretty=format:{GIT_FORMAT}"]
    if since:
        args.append(f"--since={since}")
    out = _git(repo_path, *args)
    if out is None or out.returncode != 0:
        return events.ParseResult([], 0)

    evs = []
    skipped = 0
    for line in out.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) != 4:
            skipped += 1
            continue
        commit_hash, author, author_iso, subject = parts
        evs.append({
            "schema_version": events.SCHEMA_VERSION,
            "event_id": events.make_commit_event_id(str(repo_path), commit_hash),
            "ts": author_iso, "date": events.to_local_date(author_iso),
            "tool": "git", "kind": "commit",
            "project": events.derive_project(str(repo_path)),
            "cwd": str(repo_path), "git_branch": None, "session_id": None,
            "title": subject, "summary": subject,
            "meta": {"commit": commit_hash, "author": author},
            "raw_ref": None,
        })
    return events.ParseResult(evs, skipped)
