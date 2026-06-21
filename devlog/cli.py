from __future__ import annotations

import argparse
import os
from datetime import date

from . import config, ingest as ingest_mod, report as report_mod, state as state_mod, store


def _today() -> str:
    return date.today().isoformat()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="devlog",
                                description="Self-writing AI work journal.")
    p.add_argument("--root", default=None, help="store root (overrides default/XDG)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="scan sources and update the journal")
    pi.add_argument("--strict", action="store_true",
                    help="strict validation (used to vet new Codex rollouts)")

    pr = sub.add_parser("report", help="render a daily/weekly report")
    pr.add_argument("--date", default="today", help="'today' or YYYY-MM-DD")
    pr.add_argument("--week", action="store_true", help="7-day window ending on --date")
    pr.add_argument("--ai", action="store_true", help="append an AI narrative")
    pr.add_argument("--engine", default="claude", help="claude | codex")

    sub.add_parser("rebuild", help="rebuild journal.db from events.jsonl")
    sub.add_parser("status", help="show store health and counts")

    args = p.parse_args(argv)
    paths = config.get_paths(args.root)

    if args.cmd == "ingest":
        config.ensure_dirs(paths)
        summary = ingest_mod.ingest(
            paths, strict=args.strict,
            claude_base=os.environ.get("DEVLOG_CLAUDE_BASE"),
            codex_base=os.environ.get("DEVLOG_CODEX_BASE"))
        print("ingest complete:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        return 0

    if args.cmd == "report":
        config.ensure_dirs(paths)
        target = _today() if args.date == "today" else args.date
        engine_fn = None
        if args.ai:
            from . import engine as engine_mod
            engine_fn = lambda prompt: engine_mod.run_engine(prompt, name=args.engine)
        md = report_mod.daily_report(target, paths, engine_fn=engine_fn, week=args.week)
        out_file = paths.reports / "daily" / f"{target}.md"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(md, encoding="utf-8")
        print(md, end="")
        return 0

    if args.cmd == "rebuild":
        n = store.rebuild(paths)
        print(f"rebuilt journal.db: {n} events loaded")
        return 0

    if args.cmd == "status":
        conn = store.connect(paths)
        c = store.counts(conn)
        conn.close()
        st = state_mod.load_state(paths)
        print("devlog status:")
        print(f"  root: {paths.root}")
        print(f"  total events: {c['total']}")
        print(f"  by tool: {c['by_tool']}")
        print(f"  tracked source files: {len(st)}")
        return 0

    return 1
