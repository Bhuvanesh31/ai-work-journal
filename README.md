# devlog — a self-writing AI work journal

Unifies Claude Code, Codex, and git history into one durable local log and renders
daily/weekly reports. Python stdlib only. No external API — the optional AI narrative
shells out to your local `claude`/`codex` CLI.

## Usage
    python -m devlog ingest                 # pull new history into the store
    python -m devlog report --date today    # today's report (also writes reports/daily/)
    python -m devlog report --week          # 7-day window
    python -m devlog report --ai            # add AI narrative via local claude
    python -m devlog rebuild                # rebuild the SQLite index from events.jsonl
    python -m devlog status                 # health + counts

Store lives at `$XDG_DATA_HOME/devlog/` (or `~/.local/share/devlog/`); override with
`--root PATH` or `DEVLOG_ROOT`.

## Tests
    python -m unittest discover -s devlog/tests -v
