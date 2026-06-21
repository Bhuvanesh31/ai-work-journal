import tempfile
import unittest

from devlog import config, report, store


def _session(eid, date, project, prompts, tools, dur):
    return {"schema_version": 1, "event_id": eid, "ts": f"{date}T10:00:00Z",
            "date": date, "tool": "claude", "kind": "session_day",
            "project": project, "cwd": "/x", "git_branch": None,
            "session_id": "s", "title": "t", "summary": "did work",
            "meta": {"prompt_count": prompts, "tool_use_count": sum(tools.values()),
                     "tool_breakdown": tools, "duration_min": dur},
            "raw_ref": None}


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paths = config.get_paths(self.tmp.name)
        config.ensure_dirs(self.paths)
        conn = store.connect(self.paths)
        store.append_events(self.paths, conn, [
            _session("a", "2026-06-17", "proj-one", 5, {"Bash": 3, "Edit": 1}, 40),
            _session("b", "2026-06-17", "proj-two", 2, {"Read": 2}, 10),
        ])
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_stats_and_render(self):
        md = report.daily_report(self.paths, "2026-06-17")
        self.assertIn("# Work journal — 2026-06-17", md)
        self.assertIn("Human prompts: 7", md)
        self.assertIn("Tool calls: 6", md)
        self.assertIn("**proj-one**", md)
        self.assertIn("Bash: 3", md)

    def test_ai_section_uses_injected_engine(self):
        md = report.daily_report(self.paths, "2026-06-17", ai=True,
                                 engine=lambda prompt: "NARRATIVE-OK")
        self.assertIn("## AI summary", md)
        self.assertIn("NARRATIVE-OK", md)

    def test_ai_failure_is_soft(self):
        md = report.daily_report(self.paths, "2026-06-17", ai=True,
                                 engine=lambda prompt: None)
        self.assertIn("AI summary unavailable", md)


if __name__ == "__main__":
    unittest.main()
