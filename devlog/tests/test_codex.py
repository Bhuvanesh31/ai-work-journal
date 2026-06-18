import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from devlog.parsers import codex


class CodexParserTest(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_absent_dir_yields_no_rollouts(self):
        self.assertEqual(codex.find_codex_rollouts(Path(self.tmp.name) / "nope"), [])

    def test_generic_extraction(self):
        p = Path(self.tmp.name) / "rollout-abc.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in [
                {"timestamp": "2026-06-17T08:00:00Z", "type": "message",
                 "role": "user", "content": "do a thing", "cwd": "/home/x/codex_proj"},
                {"timestamp": "2026-06-17T08:05:00Z", "type": "message",
                 "role": "assistant", "content": "done"},
            ]:
                f.write(json.dumps(r) + "\n")
        res = codex.parse_codex_rollout(p)
        self.assertEqual(len(res.events), 1)
        e = res.events[0]
        self.assertEqual(e["tool"], "codex")
        self.assertEqual(e["kind"], "session_day")
        self.assertEqual(e["date"], "2026-06-17")
        self.assertEqual(e["session_id"], "abc")
        self.assertEqual(e["project"], "codex-proj")
        self.assertEqual(e["meta"]["prompt_count"], 1)
        self.assertTrue(e["meta"]["best_effort"])


if __name__ == "__main__":
    unittest.main()
