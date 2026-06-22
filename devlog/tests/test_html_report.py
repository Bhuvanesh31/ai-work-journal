from __future__ import annotations

import tempfile
import unittest

from devlog import config, report, store
from devlog import html_report


def _session(eid, date, project, prompts, tools, dur):
    return {"schema_version": 1, "event_id": eid, "ts": f"{date}T10:00:00Z",
            "date": date, "tool": "claude", "kind": "session_day",
            "project": project, "cwd": "/x", "git_branch": None,
            "session_id": "s", "title": "t", "summary": "did work",
            "meta": {"prompt_count": prompts, "tool_use_count": sum(tools.values()),
                     "tool_breakdown": tools, "duration_min": dur},
            "raw_ref": None}


def _commit(eid, date, project, summary, sha="abc12345"):
    return {"schema_version": 1, "event_id": eid, "ts": f"{date}T11:00:00Z",
            "date": date, "tool": "git", "kind": "commit",
            "project": project, "cwd": "/x", "git_branch": "main",
            "session_id": None, "title": summary, "summary": summary,
            "meta": {"commit": sha}, "raw_ref": None}


class HtmlReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paths = config.get_paths(self.tmp.name)
        config.ensure_dirs(self.paths)
        conn = store.connect(self.paths)
        store.append_events(self.paths, conn, [
            _session("s1", "2026-06-17", "proj-alpha", 5, {"Bash": 3, "Read": 2}, 40),
            _session("s2", "2026-06-17", "proj-beta", 2, {"Edit": 1}, 10),
            _commit("c1", "2026-06-17", "proj-alpha", "feat: add widget", "aaaa1111"),
            _commit("c2", "2026-06-17", "proj-beta", "fix: broken import", "bbbb2222"),
        ])
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def _stats_and_evs(self, date="2026-06-17"):
        conn = store.connect(self.paths)
        evs = report.gather(conn, date, week=False)
        conn.close()
        return report.build_stats(evs), evs

    def test_html_contains_structural_landmarks(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs)
        self.assertIn("<!DOCTYPE html>", h)
        self.assertIn("Work Journal", h)
        self.assertIn("devlog", h)
        self.assertIn("Toggle Mode", h)

    def test_html_shows_accurate_session_count(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs)
        # 2 sessions in test data
        self.assertIn(">2<", h)

    def test_html_shows_commit_hashes_and_messages(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs)
        self.assertIn("aaaa1111", h)
        self.assertIn("feat: add widget", h)
        self.assertIn("bbbb2222", h)
        self.assertIn("fix: broken import", h)

    def test_html_escapes_special_characters(self):
        conn = store.connect(self.paths)
        store.append_events(self.paths, conn, [
            _commit("c3", "2026-06-17", "proj-alpha",
                    "fix: handle <script>alert('xss')</script>", "cccc3333"),
        ])
        conn.close()
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs)
        self.assertNotIn("<script>alert", h)
        self.assertIn("&lt;script&gt;", h)

    def test_html_detailed_shows_per_project_sections(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs, detailed=True)
        self.assertIn("proj-alpha", h)
        self.assertIn("proj-beta", h)
        # project-level stats present
        self.assertIn("Sessions", h)
        self.assertIn("Prompts", h)

    def test_html_detailed_project_stats_are_scoped(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs, detailed=True)
        # proj-alpha has Bash:3 in its tool breakdown; proj-beta has Edit:1
        # both commits should appear under their respective projects
        alpha_pos = h.index("proj-alpha")
        beta_pos = h.index("proj-beta")
        # aaaa1111 commit belongs to alpha, bbbb2222 to beta
        self.assertLess(h.index("aaaa1111"), beta_pos)

    def test_html_ai_summary_uses_injected_engine(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs,
                                    engine_fn=lambda p: "SUMMARY-TEXT")
        self.assertIn("AI Summary", h)
        self.assertIn("SUMMARY-TEXT", h)

    def test_html_ai_failure_is_soft(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs,
                                    engine_fn=lambda p: None)
        self.assertIn("unavailable", h)
        self.assertNotIn("SUMMARY-TEXT", h)

    def test_html_commit_truncation_shows_remainder(self):
        # add 20 commits so we exceed _MAX_COMMITS_GLOBAL (15)
        conn = store.connect(self.paths)
        extra = [_commit(f"cx{i}", "2026-06-17", "proj-alpha",
                         f"chore: commit {i}", f"{'%08x' % i}")
                 for i in range(20)]
        store.append_events(self.paths, conn, extra)
        conn.close()
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs)
        self.assertIn("more commit", h)

    def test_html_ai_time_label_and_note(self):
        stats, evs = self._stats_and_evs()
        h = html_report.render_html(stats, "2026-06-17", evs)
        self.assertIn("AI Session Time", h)
        self.assertIn("accumulated", h)

    def test_daily_report_emits_html_file(self):
        md = report.daily_report("2026-06-17", self.paths, emit_html=True)
        html_path = self.paths.reports / "2026-06-17.html"
        self.assertTrue(html_path.exists())
        content = html_path.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("Work Journal", content)


if __name__ == "__main__":
    unittest.main()
