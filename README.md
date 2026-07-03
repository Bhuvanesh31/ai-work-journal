# devlog — self-writing AI work journal

Ingests Claude Code sessions, Codex sessions, and git commits into a durable local store and renders daily, weekly, or monthly reports as Markdown or styled HTML. Zero external dependencies — runs entirely on Python stdlib and your local `claude`/`codex` CLI.

---

## What it does

```
~/.claude/projects/   ─┐
~/.codex/              ├─► events.jsonl (append-only) ─► journal.db ─► reports/
git repos             ─┘
```

Every `devlog ingest` snapshots new sessions and commits into a SHA-256-deduplicated event log. Reports pull from that log — no network calls, no cloud API.

---

## Install

```bash
pipx install .
```

Requires Python 3.8+. The `--ai` flag requires `claude` or `codex` on your `$PATH`.

---

## Usage

```bash
# Pull new history into the store
devlog ingest

# Reports
devlog report                               # today
devlog report --week                        # 7-day window
devlog report --month                       # 30-day window
devlog report --date 2026-06-01             # specific date

# Flags (stack freely)
devlog report --week --ai                   # add AI narrative (shells out to claude -p)
devlog report --week --detailed             # per-project stat cards
devlog report --week --detailed --ai --html # full report: markdown + self-contained HTML

# Maintenance
devlog status                               # store health + event counts
devlog rebuild                              # rebuild journal.db from events.jsonl
```

`--engine codex` switches AI narrative to Codex. `--root PATH` or `$DEVLOG_ROOT` overrides the store location.

Store lives at `$XDG_DATA_HOME/devlog/` → `~/.local/share/devlog/` by default.

---

## Report output

**Markdown** (`~/.local/share/devlog/reports/YYYY-MM-DD.md`):
- Summary stats: sessions, human prompts, tool calls, active time, commits
- Project breakdown, top tools, commit list
- Optional AI narrative (3–4 sentence summary + performance-review bullets)
- Optional per-project sections with scoped stats + AI explanation

**HTML** (same path, `.html`) adds a self-contained styled page with light/dark toggle, stat cards, and expandable project sections. Zero external dependencies — fully offline-viewable.

---

## Architecture

Three-tier durability:

| Tier | Location | Role |
|------|----------|------|
| Source | `~/.claude/`, `~/.codex/`, git repos | Read-only; never touched |
| Archive | `~/.local/share/devlog/events.jsonl` | Append-only; crash-safe |
| Index | `~/.local/share/devlog/journal.db` | SQLite; always rebuildable |

Key design choices:
- **SHA-256 event IDs** — ingest is idempotent; run it as often as you like
- **Injectable engine** — `engine.py` shells out to `claude -p`; tests inject stubs
- **No pip dependencies** — stdlib only; install anywhere

---

## Tests

```bash
python -m pytest devlog/tests/ -v
# 48 tests, all passing
```

---

## What's next

- **`devlog open`** — open today's HTML report in the browser (`xdg-open`)
- **Multi-repo git ingestion** — scan all project roots instead of just the current repo
- **Fix Codex project/cwd capture** — Codex events currently log `project: null`; patch once the log format exposes the working directory
- **`devlog digest --week`** — plain-text or HTML email digest ready to paste/send
- **Dashboard mode** — persistent local HTML page that auto-refreshes from the store

---

## License

MIT
