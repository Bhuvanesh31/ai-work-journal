# devlog — a self-writing, AI-powered work journal

**Status:** Approved design (v1)
**Date:** 2026-06-18
**Author:** bhuvanesh (revops@leadle.in)

---

## 1. Problem

Work happens across multiple Claude Code sessions, Codex sessions, and git commits
on a single Linux/Ubuntu workstation. Each tool stores its own history in its own
format and location. There is no single place that answers **"what did I actually do
this week?"** — or this day, month, or year.

The goal is an open-source CLI that pulls session history from every AI coding tool
in use into one unified, local, durable log, and generates reports from it.

## 2. Hard constraints

1. **No external API.** No Anthropic API, no OpenAI API, no metered LLM endpoint.
2. **AI engine = the local CLIs already installed.** "AI-powered" is achieved by
   shelling out to `claude -p` (and optionally `codex exec`) in non-interactive mode,
   which run on the user's existing subscription auth at zero marginal cost.
3. **Non-breakable / multi-year durability.** No single file whose loss is fatal; any
   derived state must be rebuildable from an owned, plain-text source of truth.
4. **Sources available today:** Claude Code and Codex only (plus git). Design must
   leave room for more tools later without schema breakage.

## 3. Scope

### v1 (this spec): the walking skeleton
**Ingest → unified log → daily/weekly report.** Parsers for Claude/Codex/git feed one
normalized, durable event store; a report command answers "what did I do today / this
week" with deterministic stats plus an optional AI narrative.

### Explicitly deferred (designed-for, not built in v1)
HTML dashboard · CSV/JSON export · monthly/yearly rollups · "combined brain log"
(mistakes/lessons extraction) · cron/timer installer. Each is a thin reader over the
same store; the schema and verbatim archive are designed so none of them is blocked
later.

## 4. Key decisions (resolved during brainstorming)

| Decision | Choice | Why |
|---|---|---|
| AI engine | Shell out to local `claude -p` / `codex exec`, **injectable** | Satisfies no-API constraint; keeps tool offline-testable; swappable engines |
| v1 slice | Ingest + unified log + daily report | Load-bearing foundation everything else reads from |
| Store | Verbatim archive + normalized JSONL (source of truth) + SQLite index | Three durability tiers; DB is a rebuildable cache, never the truth |
| Language | **Python, stdlib only** | Zero pip dependencies = nothing to rot; runs untouched for years |
| Automation | Manual `ingest` now, **idempotent + cron-ready** | Prove the core first; scheduling is a later one-liner |
| Granularity | **`(sessionId, calendar-day)` work blocks** | A single session file spans many days (proven: 19 active days in one file); whole-session events would be nonsensical |
| Project identity | Derived from the **line-level `cwd`**, not the folder name | Folder encoding collapses `/` and `_` both to `-` and is lossy |

## 5. Architecture & data flow

```
  Claude sessions ─┐
  Codex rollouts  ─┼─►  ingest  ─►  archive/        (verbatim copies — tier 2, owned)
  git log         ─┘                events.jsonl    (normalized, append-only — SOURCE OF TRUTH)
                                    journal.db      (SQLite index — rebuildable cache, tier 3)
                                          │
                                report ──►│──► terminal / reports/daily/*.md
                                          └──► (later: HTML, CSV, brain log)
```

**Three durability tiers:**
1. **Original tool logs** (`~/.claude/projects`, `~/.codex/sessions`) — *not owned*; may
   be rotated/deleted/reformatted by the tools. Read-only to us.
2. **Owned verbatim archive + normalized `events.jsonl`** — append-only plain text, the
   source of truth. Survives any upstream change; opens in any editor in 2030.
3. **`journal.db`** — SQLite query/aggregation cache. `rebuild` deletes and replays it
   from tier 2 in seconds. Never authoritative.

## 6. Store layout

Default root: `$XDG_DATA_HOME/devlog/` (fallback `~/.local/share/devlog/`), overridable
via `--root` / `DEVLOG_ROOT`.

```
archive/
  claude/<sessionId>.jsonl       # verbatim copy of source session — survives upstream deletion
  codex/<rolloutId>.jsonl
events.jsonl                     # normalized events, one JSON object per line, append-only
journal.db                       # SQLite index, DELETE-and-rebuild anytime
reports/
  daily/2026-06-18.md
state.json                       # ingest cursor: per-source-file -> {mtime, size, last_offset}
```

## 7. Normalized event schema

One JSON object per line in `events.jsonl`:

```json
{
  "schema_version": 1,
  "event_id": "<stable hash>",
  "ts": "2026-06-17T16:45:02+05:30",
  "date": "2026-06-17",
  "tool": "claude | codex | git",
  "kind": "session_day | commit",
  "project": "leadle-master",
  "cwd": "/home/bhuvanesh/leadle_master_claude",
  "git_branch": "feat/dashboard-fasttrack",
  "session_id": "9949e694-...",
  "title": "Analyze Leadle's lead generation and RevOps offerings",
  "summary": "first human prompt, trimmed",
  "meta": {
    "prompt_count": 14,
    "tool_use_count": 37,
    "tool_breakdown": { "Bash": 12, "Edit": 9, "Read": 6 },
    "duration_min": 92,
    "first_ts": "2026-06-17T09:01:00+05:30",
    "last_ts": "2026-06-17T16:45:02+05:30",
    "model": "claude-opus-4-7",
    "models": ["claude-opus-4-7"]
  },
  "raw_ref": "archive/claude/9949e694-....jsonl"
}
```

**Rules that protect longevity:**
- `event_id` is a stable content hash → ingest is **idempotent** (re-running never
  double-counts).
- `schema_version` + tolerant readers (ignore unknown fields, default missing ones) →
  fields can be **added** in future versions without breaking old lines.
- `raw_ref` provides provenance back to the verbatim archive, so message-level detail
  (needed by the future brain log) is never lost even though v1 events are
  session-day-level.

### Event identity
- `session_day` events: `event_id = sha1("claude|" + session_id + "|" + date)`.
- `commit` events: `event_id = sha1("git|" + repo_path + "|" + commit_hash)`.

## 8. Parsing rules (per source)

### 8.1 Claude Code — `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`
- File = one `sessionId`; read **line by line**, each line is one JSON object.
- A single file may span **many calendar days** (`--resume` appends). Bucket lines by
  `timestamp[:10]` **converted to local time** → emit one `session_day` event per
  `(sessionId, local-date)`.
- **Real human prompt** = `type=="user"` AND `message.content` is a `str` AND NOT
  `isMeta` AND NOT `isSidechain` AND content does not start with `<local-command` or
  `<command-`. (Verified: naive count 1128 → filtered 112.)
- **Tool use** = `type=="assistant"` → `message.content[]` blocks with `type=="tool_use"`
  (collect `name` for breakdown).
- `model` from `message.model` on assistant lines.
- `title` from the `aiTitle` line when present, else the first real human prompt
  (trimmed); `summary` = first real human prompt of that day.
- `project` derived from line-level `cwd` (basename, normalized), **not** the folder name.

### 8.2 git — per repo discovered under tracked `cwd`s
```
git log --no-merges --date=iso-strict --pretty=format:'%H%x1f%an%x1f%aI%x1f%s'
```
- `%x1f` = ASCII unit separator (0x1F); `line.split("\x1f")` is collision-proof.
- One `commit` event per commit; `ts`/`date` from author date (`%aI`), `summary` = `%s`.

### 8.3 Codex — `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
- Same line-by-line JSONL parse. No data exists yet; parser **no-ops gracefully** when
  the directory is absent and begins working on the first real rollout.
- First real rollout is validated via a `--strict` ingest pass before its mapping is
  trusted; until then Codex events are best-effort and clearly tagged.

### 8.4 Defensive parsing (all sources)
- Session files are **live-appended**: the last line is often a partial write. Malformed
  / truncated JSON lines are **skipped and counted**, never crash ingest.
- Timestamps are normalized: parse ISO-8601, convert UTC `Z` to local tz for `date`
  bucketing; keep original offset in `ts`.

## 9. Ingest algorithm (idempotent, resumable)

1. Discover source files (Claude project dirs, Codex session tree, git repos in tracked
   cwds).
2. For each file, consult `state.json` cursor (`mtime`, `size`, `last_offset`); skip
   unchanged files; read only appended bytes when possible.
3. Copy/refresh the verbatim file into `archive/`.
4. Parse new lines → aggregate into `(sessionId, date)` buckets / commits → build
   normalized events.
5. Append events to `events.jsonl` **only if `event_id` unseen** (dedup set seeded from
   existing DB), then upsert into `journal.db`.
6. Update `state.json` cursors last.

Crash mid-run → next run resumes from cursors; `event_id` dedup absorbs any overlap.
Sources are **read-only**; devlog never writes to `~/.claude` or `~/.codex`.

## 10. CLI (v1)

| Command | Behaviour |
|---|---|
| `devlog ingest [--strict] [--root PATH]` | Scan sources, archive raw, append new events, update DB. Idempotent, resumable. |
| `devlog report [--date today\|YYYY-MM-DD] [--week] [--ai] [--engine claude\|codex]` | Deterministic stats always; `--ai` appends narrative + performance-review bullets via the engine. |
| `devlog rebuild` | Delete `journal.db`, replay `events.jsonl`. The safety net. |
| `devlog status` | Counts, per-tool totals, last ingest time, skipped-line tally, health. |

## 11. AI layer (the no-API mechanism)

- `report --ai` builds a **compact** context (the day's `session_day` events, projects
  touched, commit subjects, counts) — not raw transcripts — and pipes it to the engine:
  `claude -p "<prompt>"` or `codex exec "<prompt>"` as a subprocess.
- Deterministic stats render with **zero** AI involvement. The AI narrative +
  performance-review bullets are appended **only** when `--ai` is set and the engine
  binary is found on `PATH`.
- Engine missing / errors / times out → stats-only output plus a one-line note. The AI
  layer **never blocks and never bills.**
- The engine is an **injected callable** (`engine(prompt:str) -> str`) so tests run fully
  offline and engines are swappable.

## 12. Error handling & durability summary

- Read-only on all sources; only `archive/`, `events.jsonl`, `journal.db`, `state.json`,
  `reports/` are written.
- Malformed lines skipped + counted (surfaced in `status`), never fatal.
- `journal.db` is disposable; `rebuild` reconstructs it from `events.jsonl`.
- `events.jsonl` append-only; never rewritten in place.
- `schema_version` + tolerant readers guarantee forward compatibility.

## 13. Testing (stdlib `unittest`)

- Pure `parse(line) -> event` / `aggregate(lines) -> events` functions tested against
  **committed fixtures** (sanitized sample Claude JSONL, a synthetic Codex rollout, a
  git-log sample).
- **Idempotency test:** ingest the same fixtures twice → identical `events.jsonl` and DB.
- **Day-bucketing test:** a multi-day session fixture → correct per-day split.
- **Prompt-filter test:** meta/sidechain/tool-result/local-command lines excluded.
- **Golden-file test:** report rendering for a fixed fixture set.
- AI path tested with a stub engine (canned text); real `claude` is never invoked in
  tests.

## 14. Project layout

```
devlog/
  __main__.py        # CLI entry (argparse)
  cli.py             # command dispatch
  parsers/
    claude.py        # Claude JSONL -> session_day events
    codex.py         # Codex rollout -> events (defensive/no-op when absent)
    gitlog.py        # git log -> commit events
  store.py           # archive copy, events.jsonl append+dedup, SQLite index, rebuild
  report.py          # deterministic stats + report rendering
  engine.py          # injectable subprocess wrapper for claude/codex
  state.py           # ingest cursors (state.json)
  tests/
    fixtures/
    test_*.py
```

## 15. Open items deferred to implementation

- Exact local-timezone source (system tz via `datetime.astimezone()`); DST handled by
  using aware datetimes.
- Which cwds to scan for git repos (start: distinct `cwd`s seen in Claude/Codex events).
- Report markdown styling (kept minimal in v1).
