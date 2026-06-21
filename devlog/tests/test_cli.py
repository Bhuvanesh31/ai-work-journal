import io
import json
import os
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from devlog import cli


class CliTest(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "store"
        self.claude_base = Path(self.tmp.name) / "claude_projects" / "-home-x-proj"
        self.claude_base.mkdir(parents=True)
        with open(self.claude_base / "sess-1.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "timestamp": "2026-06-17T09:00:00Z",
                                "cwd": "/home/x/proj",
                                "message": {"role": "user", "content": "hello"}}) + "\n")
        os.environ["DEVLOG_CLAUDE_BASE"] = str(self.claude_base.parent)
        os.environ["DEVLOG_CODEX_BASE"] = str(Path(self.tmp.name) / "no_codex")

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("DEVLOG_CLAUDE_BASE", None)
        os.environ.pop("DEVLOG_CODEX_BASE", None)

    def _run(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(["--root", str(self.root), *args])
        return code, buf.getvalue()

    def test_ingest_then_report_then_status(self):
        code, out = self._run("ingest")
        self.assertEqual(code, 0)
        self.assertIn("events_added", out)

        code, out = self._run("report", "--date", "2026-06-17")
        self.assertEqual(code, 0)
        self.assertIn("# Work journal — 2026-06-17", out)
        self.assertTrue((self.root / "reports" / "daily" / "2026-06-17.md").exists())

        code, out = self._run("status")
        self.assertEqual(code, 0)
        self.assertIn("total", out.lower())

    def test_rebuild(self):
        self._run("ingest")
        code, out = self._run("rebuild")
        self.assertEqual(code, 0)
        self.assertIn("rebuilt", out.lower())


if __name__ == "__main__":
    unittest.main()
