from __future__ import annotations

import shutil
import subprocess


def engine_available(name: str = "claude") -> bool:
    return shutil.which(name) is not None


def run_engine(prompt: str, name: str = "claude", timeout: int = 120) -> str | None:
    exe = shutil.which(name)
    if not exe:
        return None
    if name == "codex":
        cmd = [exe, "exec", prompt]
    else:  # claude and anything claude-like
        cmd = [exe, "-p", prompt]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None
