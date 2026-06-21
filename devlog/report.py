from __future__ import annotations

from collections import Counter
from datetime import date as date_cls, timedelta

from . import store
from . import engine as engine_mod


def gather(conn, target_date: str, week: bool = False):
    if week:
        end = date_cls.fromisoformat(target_date)
        start = end - timedelta(days=6)
        return store.query_range(conn, start.isoformat(), end.isoformat())
    return store.query_range(conn, target_date, target_date)


def build_stats(evs) -> dict:
    sessions = [e for e in evs if e["kind"] == "session_day"]
    commits = [e for e in evs if e["kind"] == "commit"]
    projects: Counter = Counter()
    tools: Counter = Counter()
    prompts = tool_use = duration = 0
    for e in sessions:
        if e.get("project"):
            projects[e["project"]] += 1
        m = e.get("meta", {})
        prompts += m.get("prompt_count", 0)
        tool_use += m.get("tool_use_count", 0)
        duration += m.get("duration_min", 0)
        for k, v in (m.get("tool_breakdown") or {}).items():
            tools[k] += v
    return {"sessions": sessions, "commits": commits, "projects": projects,
            "tools": tools, "prompts": prompts, "tool_use": tool_use,
            "duration_min": duration}


def render_markdown(stats: dict, label: str) -> str:
    lines = [f"# Work journal — {label}", ""]
    lines.append(f"- Sessions: {len(stats['sessions'])}")
    lines.append(f"- Human prompts: {stats['prompts']}")
    lines.append(f"- Tool calls: {stats['tool_use']}")
    lines.append(f"- Active time (approx): {stats['duration_min']} min")
    lines.append(f"- Commits: {len(stats['commits'])}")
    lines.append("")
    if stats["projects"]:
        lines.append("## Projects")
        for proj, n in sorted(stats["projects"].items()):
            lines.append(f"- **{proj}**: {n} session-day(s)")
        lines.append("")
    if stats["tools"]:
        lines.append("## Top tools")
        for name, n in stats["tools"].most_common(8):
            lines.append(f"- {name}: {n}")
        lines.append("")
    if stats["commits"]:
        lines.append("## Commits")
        for c in stats["commits"]:
            short = (c.get("meta", {}).get("commit", "") or "")[:8]
            lines.append(f"- `{short}` {c['summary']} ({c.get('project')})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_ai_prompt(stats: dict, label: str) -> str:
    proj = ", ".join(f"{p} ({n})" for p, n in sorted(stats["projects"].items())) or "none"
    commits = "\n".join(f"- {c['summary']}" for c in stats["commits"]) or "(none)"
    return (
        "You are writing a concise work-journal entry. Based ONLY on the data below, "
        f"write a 3-4 sentence narrative of what was accomplished ({label}), then 3-5 "
        "impact-oriented performance-review bullet points. Do not invent specifics.\n\n"
        f"Sessions: {len(stats['sessions'])}, prompts: {stats['prompts']}, "
        f"tool calls: {stats['tool_use']}, commits: {len(stats['commits'])}.\n"
        f"Projects: {proj}.\nCommit messages:\n{commits}\n"
    )


def daily_report(paths, target_date: str, week=False, ai=False, engine=None) -> str:
    conn = store.connect(paths)
    try:
        evs = gather(conn, target_date, week)
    finally:
        conn.close()
    stats = build_stats(evs)
    label = f"week ending {target_date}" if week else target_date
    md = render_markdown(stats, label)
    if ai:
        eng = engine if engine is not None else (lambda prompt: engine_mod.run_engine(prompt))
        text = eng(build_ai_prompt(stats, label))
        if text:
            md += "\n## AI summary\n\n" + text.strip() + "\n"
        else:
            md += ("\n_(AI summary unavailable — engine not found or failed; "
                   "stats above are complete.)_\n")
    return md
