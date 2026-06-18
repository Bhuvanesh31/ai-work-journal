import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from devlog.parsers import claude


def _write(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


class ClaudeParserTest(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sess-1.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_buckets_by_day_and_filters_prompts(self):
        _write(self.path, [
            {"type": "ai-title", "aiTitle": "Build the thing"},
            {"type": "user", "timestamp": "2026-06-17T09:00:00Z",
             "cwd": "/home/x/proj_one", "gitBranch": "main",
             "message": {"role": "user", "content": "real prompt one"}},
            {"type": "user", "timestamp": "2026-06-17T09:01:00Z", "isMeta": True,
             "message": {"role": "user", "content": "<local-command-stdout>noise"}},
            {"type": "user", "timestamp": "2026-06-17T09:02:00Z",
             "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}},
            {"type": "assistant", "timestamp": "2026-06-17T09:03:00Z",
             "message": {"role": "assistant", "model": "claude-opus-4-7",
                         "content": [{"type": "tool_use", "name": "Bash"},
                                     {"type": "tool_use", "name": "Edit"}]}},
            {"type": "user", "timestamp": "2026-06-18T10:00:00Z",
             "cwd": "/home/x/proj_one",
             "message": {"role": "user", "content": "next day prompt"}},
        ])
        res = claude.parse_claude_session(self.path)
        self.assertEqual(res.skipped, 0)
        by_date = {e["date"]: e for e in res.events}
        self.assertEqual(set(by_date), {"2026-06-17", "2026-06-18"})

        d17 = by_date["2026-06-17"]
        self.assertEqual(d17["kind"], "session_day")
        self.assertEqual(d17["session_id"], "sess-1")
        self.assertEqual(d17["project"], "proj-one")
        self.assertEqual(d17["title"], "Build the thing")
        self.assertEqual(d17["summary"], "real prompt one")
        self.assertEqual(d17["meta"]["prompt_count"], 1)  # meta + tool_result excluded
        self.assertEqual(d17["meta"]["tool_use_count"], 2)
        self.assertEqual(d17["meta"]["tool_breakdown"], {"Bash": 1, "Edit": 1})
        self.assertEqual(d17["meta"]["model"], "claude-opus-4-7")
        self.assertEqual(d17["raw_ref"], "archive/claude/sess-1.jsonl")

    def test_skips_malformed_lines(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('{"type":"user","timestamp":"2026-06-17T09:00:00Z",'
                    '"message":{"role":"user","content":"ok"}}\n')
            f.write('{ this is not json\n')  # partial/truncated last line
        res = claude.parse_claude_session(self.path)
        self.assertEqual(res.skipped, 1)
        self.assertEqual(len(res.events), 1)


if __name__ == "__main__":
    unittest.main()
