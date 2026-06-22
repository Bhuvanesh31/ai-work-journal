# devlog — Project Status
> Last updated: 2026-06-23

---

## What Is This?

**devlog** is a zero-effort, self-writing AI work journal CLI. It ingests Claude Code transcripts, Codex session logs, and git commits — then generates structured markdown and HTML daily/weekly reports. No manual writing required. No cloud API calls. Runs entirely from local CLI tools.

Install: `pipx install .`  
Run: `devlog ingest && devlog report --week --detailed --ai --html`

---

## Current Architecture

### Three-tier durability model

```
[source logs]          [verbatim archive + events.jsonl]     [SQLite]
~/.claude/projects/  →  ~/.local/share/devlog/archive/    →  journal.db
~/.codex/            →  ~/.local/share/devlog/events.jsonl   (rebuildable)
git repos            →
```

- **Tier 1 (source):** Raw tool logs — read-only, never touched
- **Tier 2 (archive):** Verbatim copies + append-only `events.jsonl` — crash-safe, the source of truth
- **Tier 3 (index):** `journal.db` SQLite — query-optimised, always rebuildable from Tier 2 via `devlog rebuild`

### Injectable engine pattern

All AI calls go through `engine.py` which shells out to `claude -p` (or `codex exec`). Tests inject stub functions instead. No external API SDK is ever imported.

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

## Shipped Features

| Commit | Date | Feature |
|--------|------|---------|
| `6f6198c` | 2026-06-22 | **devlog v1** — full pipeline: parsers, store, state, ingest, report, CLI |
| `18bde13` | 2026-06-22 | `pyproject.toml` + `devlog` entry point via `pipx` |
| `f27cc6f` | 2026-06-22 | `--detailed` flag — per-project stat cards + optional AI explanation per project |
| `b99ab24` | 2026-06-22 | `--html` flag — styled HTML report using Purple Studio design system |

### Full CLI surface

```bash
devlog ingest                                       # scan sources, update journal
devlog report --week                                # 7-day markdown report
devlog report --week --ai                           # + top-level AI narrative (claude -p)
devlog report --week --detailed                     # + per-project stats cards
devlog report --week --detailed --ai                # + AI narrative per project
devlog report --week --detailed --ai --html         # + self-contained HTML file
devlog status                                       # store health + event counts
devlog rebuild                                      # rebuild journal.db from events.jsonl
```

`--date YYYY-MM-DD` is also supported on `report` for any past date. `--engine codex` switches the AI provider.

---

## Test Suite

**47 tests — all passing.** Run: `python -m pytest devlog/tests/ -v`

| Test file | Count | What it covers |
|-----------|------:|----------------|
| `test_html_report.py` | 11 | HTML structure, XSS escaping, commit truncation, per-project sections, AI injection/failure, `emit_html` file write |
| `test_report.py` | 8 | Stats builder, markdown render, AI prompt, per-project detail, engine injection/failure |
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

The HTML output uses **Purple Studio** — Bhuvanesh's personal design system at:  
`/home/bhuvanesh/AI_Native_Workspace/40-personal-systems/bhuvanesh_content_studio/design-system/`

The CSS tokens from `foundation/tokens.css` are **bundled inline** into `html_report.py` (line 13–74) so generated `.html` files are fully self-contained — no external file dependencies, viewable offline.

**Two visual modes** toggled via a button in the top bar:
- **Antigravity** (default): dark glass, ink `#0F0F0F`, frosted glass cards, violet `#5B21B6` accent
- **Brutalism**: cream `#F4F1EB`, hard 3px borders, box-shadow offsets, no blur

---

## Key Technical Constraints

1. **Zero pip dependencies** — Python 3.8+ stdlib only (`pathlib`, `sqlite3`, `json`, `html`, `subprocess`, `hashlib`, `argparse`). `pipx install .` works with no conflict in any environment.
2. **No cloud API calls** — all AI calls shell out to `claude -p` or `codex exec` locally. No `anthropic` or `openai` SDK imports anywhere.
3. **Idempotent ingest** — running `devlog ingest` multiple times produces no duplicate events (SHA-256 event IDs).
4. **Rebuildable store** — `journal.db` can be deleted and regenerated at any time from `events.jsonl`.

---

## Challenges Faced

### 1. Context window exhaustion during development
The original Claude Code session ran out of context while working on the HTML sample build. All code and tests were already committed at that point, so no work was lost — but the conversation had to be resumed from summary.

**Mitigation:** Key architecture decisions and conventions are persisted in memory files at `~/.claude/projects/.../memory/`.

### 2. No editable pip install on modern Ubuntu
`pip install -e .` is blocked by PEP 668 on Debian/Ubuntu. Using `pipx install --force .` after any code change reinstalls into the existing pipx venv cleanly.

### 3. `html` is a stdlib module name
Named the parameter `emit_html` (not `html`) in `daily_report()` to avoid shadowing the stdlib `import html` used for XSS escaping in `html_report.py`.

### 4. CSS token bundling
The HTML report needs to be self-contained (shareable as a single file). This means the Purple Studio CSS tokens must be copied into `html_report.py` rather than linked. If the design system changes, both `foundation/tokens.css` and the inline copy in `html_report.py` (line 13) need updating.

### 5. Accumulated AI session time vs. wall-clock time
Claude Code tracks `duration_min` per session independently — running two projects simultaneously means both count their time. The "AI Session Time" stat in the HTML report can exceed 24h/day for a single calendar day. Added a note: `accumulated · may exceed 24h/day`.

---

## Current State (as of 2026-06-23)

- **Branch:** `master`
- **Remote:** `https://github.com/Bhuvanesh31/ai-work-journal.git` — in sync, all features merged
- **Last commit:** `b99ab24 feat: --html flag generates styled HTML report using Purple Studio design system`
- **Tests:** 47/47 passing
- **Git working tree:** clean (only `__pycache__` and build artifacts untracked)
- **pipx:** installed at `~/.local/bin/devlog`

The tool is **functional and installable**. The HTML report is fully styled and passes all tests. The last conversation ended while generating a live sample build from real week data — that never got committed (it's runtime output, not source code), so the task is simply to run it.

---

## What's Pending

### Immediate (next session)

1. **Run a live sample build** — the prior session ended here. Steps:
   ```bash
   devlog ingest
   devlog report --week --detailed --ai --html
   # → opens/views ~/.local/share/devlog/reports/<date>.html
   ```
   This is just a demo run, not code to write.

2. **Add `.gitignore`** — `ai_work_journal.egg-info/`, `build/`, and `__pycache__/` show up as untracked noise in `git status`. A one-line fix.

### Near-term improvements (no blockers, decided in prior session)

3. **Codex parser hardening** — `parsers/codex.py` is provisional. Real Codex rollout data hasn't been validated against the parser. `--strict` flag exists but needs a real corpus test.

4. **Ingest from multiple git repos** — currently `parsers/gitlog.py` only parses the repo at `cwd`. Could scan all known project directories to pick up commits from non-active repos.

5. **`devlog open` command** — convenience command to open today's `.html` report in the browser (`xdg-open` / `open`).

### Longer-term (ideas, not committed)

6. **Weekly digest email** — `devlog digest --week` that formats a plain-text or HTML email body ready to paste.

7. **Dashboard mode** — persistent HTML page that auto-refreshes from the store (local Python server), instead of a static snapshot.

8. **Codex integration test** — add a `test_codex_real_format.py` with a sample Codex session fixture once the real log format stabilises.

---

## Plan to Complete the Pending Items

### Step 1 — Gitignore (5 min)

```bash
# In project root
cat >> .gitignore << 'EOF'
__pycache__/
*.egg-info/
build/
dist/
EOF
git add .gitignore && git commit -m "chore: add .gitignore"
git push
```

### Step 2 — Live sample run (10 min)

```bash
devlog ingest
devlog report --week --detailed --ai --html --date $(date +%Y-%m-%d)
# Then open the .html file from ~/.local/share/devlog/reports/
```

This validates the full pipeline against real data and produces the sample Bhuvanesh asked for.

### Step 3 — Codex parser validation (future, when real logs are available)

Once Codex sessions generate logs at `~/.codex/`, run `devlog ingest --strict` and verify no errors. Fix any schema mismatches in `parsers/codex.py`.

### Step 4 — `devlog open` command (30 min, optional)

Add a `sub.add_parser("open")` in `cli.py` that resolves today's `.html` path and calls `subprocess.run(["xdg-open", str(html_path)])`. Tests: mock `subprocess.run`, assert the right path is passed.

---

## GitHub

`https://github.com/Bhuvanesh31/ai-work-journal`  
Branch: `master` — all features current, CI: none yet.
