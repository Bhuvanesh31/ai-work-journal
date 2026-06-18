from __future__ import annotations

from pathlib import Path

from . import config, state as statemod, store
from .parsers import claude as claudep
from .parsers import codex as codexp
from .parsers import gitlog


def discover_claude_sessions(base=None):
    base = Path(base) if base is not None else Path.home() / ".claude" / "projects"
    if not base.exists():
        return []
    return sorted(base.rglob("*.jsonl"))


def discover_git_repos(cwds):
    tops = []
    seen = set()
    for cwd in cwds:
        if not cwd or not Path(cwd).exists():
            continue
        top = gitlog.repo_toplevel(cwd)
        if top and top not in seen:
            seen.add(top)
            tops.append(top)
    return tops


def ingest(paths=None, strict=False, claude_base=None, codex_base=None) -> dict:
    paths = paths or config.get_paths()
    config.ensure_dirs(paths)
    conn = store.connect(paths)
    st = statemod.load_state(paths)
    summary = {"claude_files": 0, "codex_files": 0, "git_repos": 0,
               "events_added": 0, "skipped_lines": 0}

    for f in discover_claude_sessions(claude_base):
        summary["claude_files"] += 1
        if statemod.is_unchanged(st, f):
            continue
        store.archive_file(paths, "claude", f)
        res = claudep.parse_claude_session(f)
        summary["events_added"] += store.append_events(paths, conn, res.events)
        summary["skipped_lines"] += res.skipped
        statemod.mark(st, f)

    for f in codexp.find_codex_rollouts(codex_base):
        summary["codex_files"] += 1
        if statemod.is_unchanged(st, f):
            continue
        store.archive_file(paths, "codex", f)
        res = codexp.parse_codex_rollout(f)
        summary["events_added"] += store.append_events(paths, conn, res.events)
        summary["skipped_lines"] += res.skipped
        statemod.mark(st, f)

    for repo in discover_git_repos(store.distinct_cwds(conn)):
        summary["git_repos"] += 1
        res = gitlog.parse_git_log(repo)
        summary["events_added"] += store.append_events(paths, conn, res.events)

    statemod.save_state(paths, st)
    conn.close()
    return summary
