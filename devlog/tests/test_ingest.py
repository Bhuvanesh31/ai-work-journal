from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from devlog import config, ingest, store


class IngestTest(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.paths = config.get_paths(str(root / "store"))
        # fake claude projects tree
        self.claude_base = root / "claude_projects" / "-home-x-proj"
        self.claude_base.mkdir(parents=True)
        sess = self.claude_base / "sess-1.jsonl"
        with open(sess, "w", encoding="utf-8") as f:
            for r in [
                {"type": "user", "timestamp": "2026-06-17T09:00:00Z",
                 "cwd": "/home/x/proj",
                 "message": {"role": "user", "content": "hello"}},
                {"type": "assistant", "timestamp": "2026-06-17T09:01:00Z",
                 "message": {"role": "assistant", "model": "m",
                             "content": [{"type": "tool_use", "name": "Bash"}]}},
            ]:
                f.write(json.dumps(r) + "\n")
        self.codex_base = root / "codex_sessions"  # absent on purpose

    def tearDown(self):
        self.tmp.cleanup()

    def test_ingest_is_idempotent(self):
        s1 = ingest.ingest(self.paths, claude_base=self.claude_base.parent,
                           codex_base=self.codex_base)
        self.assertEqual(s1["claude_files"], 1)
        self.assertEqual(s1["events_added"], 1)
        # second run: unchanged file skipped, nothing added
        s2 = ingest.ingest(self.paths, claude_base=self.claude_base.parent,
                           codex_base=self.codex_base)
        self.assertEqual(s2["events_added"], 0)
        # archive copy exists
        self.assertTrue((self.paths.claude_archive / "sess-1.jsonl").exists())
        conn = store.connect(self.paths)
        self.assertEqual(store.counts(conn)["total"], 1)


if __name__ == "__main__":
    unittest.main()
