from __future__ import annotations

import json
from pathlib import Path


def load_state(paths) -> dict:
    if paths.state.exists():
        try:
            return json.loads(paths.state.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(paths, state: dict) -> None:
    paths.state.write_text(json.dumps(state, indent=1), encoding="utf-8")


def file_signature(path) -> dict:
    st = Path(path).stat()
    return {"mtime": st.st_mtime, "size": st.st_size}


def is_unchanged(state: dict, path) -> bool:
    prev = state.get(str(path))
    if not prev:
        return False
    sig = file_signature(path)
    return prev.get("mtime") == sig["mtime"] and prev.get("size") == sig["size"]


def mark(state: dict, path) -> None:
    state[str(path)] = file_signature(path)
