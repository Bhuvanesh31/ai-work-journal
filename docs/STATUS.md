# devlog — Project Status
> Last updated: 2026-07-02

---

## What Is This?

**devlog** is a zero-effort, self-writing AI work journal CLI. It ingests Claude Code transcripts, Codex session logs, and git commits — then generates structured markdown and HTML daily/weekly reports. No manual writing. No cloud API calls. Runs entirely from local CLI tools.

```bash
pipx install .
devlog ingest && devlog report --week --detailed --ai --html
```

---

## Current State (as of 2026-07-02)

| Item | Status |
|------|--------|
| Branch | `master` |
| Remote | `https://github.com/Bhuvanesh31/ai-work-journal.git` — in sync |
| Tests | **48/48 passing** (`python -m pytest devlog/tests/ -v`) |
| Live store | **966 events** ingested (670 Claude + 3 Codex + 293 git) |
| Reports generated | 2× `.md`, 1× `.html` |
| pipx install | `~/.local/bin/devlog` — working |
| Working tree | Clean (only `__pycache__` untracked, covered by `.gitignore`) |

---

## Architecture

### Three-tier durability model

```
[source logs]              [archive + events.jsonl]             [SQLite]
~/.claude/projects/   →   ~/.local/share/devlog/archive/   →   journal.db
~/.codex/             →   ~/.local/share/devlog/events.jsonl   (rebuildable)
git repos             →
```

- **Tier 1 (source):** Raw tool logs — read-only, never touched
- **Tier 2 (archive):** Verbatim copies + append-only `events.jsonl` — crash-safe
- **Tier 3 (index):** `journal.db` — query-optimised, always rebuildable via `devlog rebuild`

### Injectable engine pattern

All AI calls go through `engine.py` which shells out to `claude -p`. Tests inject stub functions. No external API SDK is imported.

### Key files

| File | Lines | Role |
|------|------:|------|
| `devlog/html_report.py` | 555 | HTML report (Purple Studio design system, self-contained) |
| `devlog/report.py` | 160 | Markdown report + stats builder |
| `devlog/store.py` | 122 | SQLite store, idempotent append, rebuild |
| `devlog/parsers/claude.py` | 115 | Claude Code transcript → events |
| `devlog/cli.py` | 83 | argparse CLI + entry point |
| `devlog/parsers/codex.py` | 74 | Codex session → events |
| `devlog/ingest.py` | 67 | Ingest orchestration |
| `devlog/config.py` | 58 | XDG-aware path resolution |
| `devlog/parsers/gitlog.py` | 55 | `git log` → commit events |
| `devlog/events.py` | 37 | Event schema + stable ID helpers |
| `devlog/state.py` | 34 | Incremental ingest cursors (mtime-based) |
| `devlog/engine.py` | 25 | Local CLI wrapper (claude / codex) |

---

## Shipped Features (all on `master`)

| Commit | Date | Feature |
|--------|------|---------|
| `6f6198c` | 2026-06-22 | devlog v1 — full pipeline: parsers, store, state, ingest, report, CLI |
| `18bde13` | 2026-06-22 | `pyproject.toml` + `devlog` entry point via `pipx` |
| `f27cc6f` | 2026-06-22 | `--detailed` flag — per-project stat cards + optional AI explanation |
| `b99ab24` | 2026-06-22 | `--html` flag — styled HTML report using Purple Studio design system |
| `5ae7dac` | 2026-06-23 | `.gitignore` + `docs/STATUS.md` |
| `f220138` | 2026-06-23 | `docs/SESSION_SUMMARY.md` — all 53 Claude session breakdown |
| `ff8344c` | 2026-07-02 | `--month` flag — 30-day window ending on `--date` |

### Full CLI surface

```bash
devlog ingest                                       # scan sources, update journal
devlog report                                       # today's report
devlog report --week                                # 7-day markdown report
devlog report --month                               # 30-day markdown report
devlog report --week --ai                           # + top-level AI narrative (claude -p)
devlog report --week --detailed                     # + per-project stats cards
devlog report --week --detailed --ai                # + AI narrative per project
devlog report --week --detailed --ai --html         # + self-contained HTML file
devlog status                                       # store health + event counts
devlog rebuild                                      # rebuild journal.db from events.jsonl
```

`--date YYYY-MM-DD` supported on `report`. `--engine codex` switches AI provider.

---

## Live Data in the Store

`~/.local/share/devlog/events.jsonl` — **966 events** spanning **2026-05-05 → 2026-06-24** (51 days).

### Event breakdown

| Tool | Kind | Count |
|------|------|------:|
| Claude Code | `session_day` | 670 |
| git | `commit` | 293 |
| Codex | `session_day` | 3 |
| **Total** | | **966** |

### Aggregate stats (all-time)

| Metric | Value |
|--------|------:|
| AI sessions | 673 |
| Human prompts | 818 |
| Tool calls | 10,294 |
| Active AI time | 20,235 min (~337 h accumulated) |
| Git commits | 293 |
| Source files tracked | 681 |

### Top projects (by session count)

| Project | Sessions |
|---------|--------:|
| leadle-gtm-intelligence | 261 |
| agentops-core | 193 |
| ai-native-work-brain | 116 |
| leadle-master-claude | 96 |
| ai-work-journal | 88 |
| ai-native-plans | 83 |
| reports | 47 |
| claude-sessions-project | 29 |
| leadle-client-dashboard | 15 |
| bhuvanesh-content-studio | 12 |

---

## Exports Generated

Reports live at `~/.local/share/devlog/reports/`.

### Files on disk

| File | Size | Date covered | Contents |
|------|------|-------------|---------|
| `2026-06-21.md` | 12 KB | 2026-06-21 | Daily markdown — sessions, commits, top tools |
| `2026-06-22.md` | 53 KB | week ending 2026-06-22 | Full weekly markdown with per-project breakdown |
| `2026-06-22.html` | 48 KB | week ending 2026-06-22 | Self-contained HTML — Purple Studio, light/dark toggle |

### What each export contains

**Markdown reports** (`*.md`):
- Summary stats: session count, human prompts, tool calls, active time, commit count
- Projects: each active project with session count
- Top tools: most-used Claude Code tools ranked by call count
- Commits: each commit with short SHA + message + project
- AI summary (if `--ai`): 3–4 sentence narrative + 3–5 bullet performance review
- Per-project detail blocks (if `--detailed`): scoped stats, top tools, commits, AI explanation

**HTML report** (`*.html`) adds:
- Purple Studio design system (Antigravity dark / Brutalism cream, toggled via top bar button)
- Stat cards with icons for all top-level metrics
- Per-project expandable cards with scoped breakdowns
- All CSS bundled inline — fully self-contained, shareable, viewable offline
- `accumulated · may exceed 24h/day` note (parallel sessions each count full duration)

### Event schema

**`session_day` event** (from Claude Code):
```json
{
  "schema_version": 1,
  "event_id": "<sha256 of source path + ts>",
  "ts": "2026-06-22T15:30:00.000Z",
  "date": "2026-06-22",
  "tool": "claude",
  "kind": "session_day",
  "project": "leadle-gtm-intelligence",
  "cwd": "/home/bhuvanesh/AI_Native_Workspace/...",
  "git_branch": "main",
  "session_id": "<uuid>",
  "title": "(first user message or untitled session)",
  "summary": "",
  "meta": {
    "prompt_count": 12,
    "tool_use_count": 87,
    "tool_breakdown": { "Bash": 34, "Read": 22, "Edit": 18 },
    "duration_min": 45,
    "first_ts": "2026-06-22T14:45:00.000Z",
    "last_ts": "2026-06-22T15:30:00.000Z",
    "model": "claude-sonnet-4-6",
    "models": ["claude-sonnet-4-6"]
  },
  "raw_ref": "archive/claude/<session_id>.jsonl"
}
```

**`commit` event** (from git):
```json
{
  "schema_version": 1,
  "event_id": "<sha256 of commit hash>",
  "ts": "2026-06-22T01:22:34+05:30",
  "date": "2026-06-22",
  "tool": "git",
  "kind": "commit",
  "project": "agentops-core",
  "cwd": "/home/bhuvanesh/AI_Native_Workspace/...",
  "git_branch": null,
  "session_id": null,
  "title": "feat: backfill_usage_metrics + maintenance subcommands",
  "summary": "feat: backfill_usage_metrics + maintenance subcommands",
  "meta": {
    "commit": "9d1eabe80305f045362b7d7c9edab3fb0eb6d219",
    "author": "Bhuvanesh"
  },
  "raw_ref": null
}
```

**`session_day` event** (from Codex — partial, `project`/`cwd` not captured yet):
```json
{
  "tool": "codex",
  "kind": "session_day",
  "project": null,
  "cwd": null,
  "meta": {
    "prompt_count": 0,
    "msg_count": 272,
    "first_ts": "...",
    "last_ts": "...",
    "best_effort": true
  }
}
```

---

## Test Suite

**48 tests — all passing.** `python -m pytest devlog/tests/ -v`

| Test file | Count | What it covers |
|-----------|------:|----------------|
| `test_html_report.py` | 11 | HTML structure, XSS escaping, commit truncation, per-project sections, AI injection/failure, `emit_html` file write |
| `test_report.py` | 9 | Stats builder, markdown render, AI prompt, per-project detail, engine injection/failure, month window |
| `test_store.py` | 4 | Idempotent append, archive copy, query range, rebuild |
| `test_events.py` | 5 | Stable event IDs, project derivation from CWD, timestamp parsing |
| `test_state.py` | 3 | Cursor persist, change detection, idempotent mark |
| `test_ingest.py` | 1 | End-to-end idempotency |
| `test_cli.py` | 2 | Full CLI pipeline (ingest → report → status, rebuild) |
| `test_claude.py` | 3 | Claude parser: day-bucketing, malformed line skips |
| `test_codex.py` | 2 | Codex parser: absent dir, generic extraction |
| `test_gitlog.py` | 3 | Git parser: missing repo, subject parsing, toplevel |
| `test_config.py` | 3 | Dir tree creation, XDG env, explicit root override |
| `test_engine.py` | 2 | `which` check, missing engine returns None |

---

## Design System

HTML output uses **Purple Studio** — CSS tokens bundled inline into `html_report.py` (lines 13–74) so `.html` files have zero external dependencies.

- **Antigravity** (default): dark glass, ink `#0F0F0F`, violet `#5B21B6` accent
- **Brutalism**: cream `#F4F1EB`, hard 3px borders, box-shadow offsets

Source at: `/home/bhuvanesh/AI_Native_Workspace/40-personal-systems/bhuvanesh_content_studio/design-system/`  
If `foundation/tokens.css` changes there, update the inline copy in `html_report.py:13` too.

---

## What's Pending

### 1 — Generate live AI report (immediate, ~5 min)

The store has 966 events but `--ai` has never been run against real data. Run:

```bash
devlog report --week --detailed --ai --html --date 2026-06-25
# → ~/.local/share/devlog/reports/2026-06-25.html
```

This triggers 1 global + N per-project `claude -p` calls and produces the first real AI-narrated HTML report.

### 2 — Fix Codex `project`/`cwd` capture (near-term)

Codex `session_day` events have `project: null` and `cwd: null` — the Codex log format (`~/.codex/`) doesn't expose the working directory. Check if newer Codex log versions include `cwd` or `git_root` fields, then update `parsers/codex.py`.

### 3 — `devlog open` command (near-term, ~30 min)

Opens today's HTML report in the browser. Add to `cli.py`:

```python
p = sub.add_parser("open")
# handler: resolve paths.reports / f"{today}.html", subprocess.run(["xdg-open", str(html_path)])
```

### 4 — Multi-repo git ingestion (near-term)

`parsers/gitlog.py` only reads the repo at `cwd`. Should scan all known project roots under `~/AI_Native_Workspace/` to pick up commits from repos not currently active.

### 5 — Weekly digest (longer-term)

`devlog digest --week` formats a plain-text or HTML email body ready to paste.

### 6 — Dashboard mode (longer-term)

Persistent HTML page that auto-refreshes from the store via a local Python server.

---

## Plan to Complete Pending Items

### Step 1 — Live AI report (now, 5 min)

```bash
devlog ingest  # pick up any new sessions from today
devlog report --week --detailed --ai --html --date 2026-06-25
xdg-open ~/.local/share/devlog/reports/2026-06-25.html
```

### Step 2 — `devlog open` command (next session, 30 min)

1. Add `open` subparser to `cli.py`
2. Resolve `paths.reports / f"{today}.html"`, call `subprocess.run(["xdg-open", ...])`
3. Add test: mock `subprocess.run`, assert correct path passed
4. `pipx install --force .` and manually test

### Step 3 — Codex `project`/`cwd` (when real Codex logs available)

1. Inspect a current `~/.codex/` log file for any `cwd` or `repo` field
2. If present, patch `parsers/codex.py` to extract it
3. Add fixture to `test_codex.py` covering the new field

### Step 4 — Multi-repo git (future, ~2 h)

1. Add `--git-roots` config option or auto-discover `~/AI_Native_Workspace/**/.git`
2. Update `ingest.py` to iterate roots
3. Update state tracking to cursor per root path

---

## GitHub

`https://github.com/Bhuvanesh31/ai-work-journal`  
Branch: `master` — all features current, CI: none yet.
