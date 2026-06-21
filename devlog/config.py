from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Paths:
    root: Path

    @property
    def archive(self) -> Path:
        return self.root / "archive"

    @property
    def claude_archive(self) -> Path:
        return self.archive / "claude"

    @property
    def codex_archive(self) -> Path:
        return self.archive / "codex"

    @property
    def events(self) -> Path:
        return self.root / "events.jsonl"

    @property
    def db(self) -> Path:
        return self.root / "journal.db"

    @property
    def state(self) -> Path:
        return self.root / "state.json"

    @property
    def reports(self) -> Path:
        return self.root / "reports"


def resolve_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("DEVLOG_ROOT")
    if env:
        return Path(env).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "devlog"


def get_paths(explicit: str | None = None) -> Paths:
    return Paths(root=resolve_root(explicit))


def ensure_dirs(paths: Paths) -> None:
    for d in (paths.root, paths.claude_archive, paths.codex_archive, paths.reports / "daily"):
        d.mkdir(parents=True, exist_ok=True)
