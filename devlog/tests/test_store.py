import os
import tempfile
import unittest
from pathlib import Path

from devlog import config, store


def _ev(eid, date="2026-06-17", tool="claude", kind="session_day", cwd="/home/x/p"):
    return {"schema_version": 1, "event_id": eid, "ts": f"{date}T10:00:00Z",
            "date": date, "tool": tool, "kind": kind, "project": "p",
            "cwd": cwd, "git_branch": None, "session_id": "s",
            "title": "t", "summary": "s", "meta": {"prompt_count": 2},
            "raw_ref": None}


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paths = config.get_paths(self.tmp.name)
        config.ensure_dirs(self.paths)

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_is_idempotent(self):
        conn = store.connect(self.paths)
        evs = [_ev("a"), _ev("b")]
        self.assertEqual(store.append_events(self.paths, conn, evs), 2)
        self.assertEqual(store.append_events(self.paths, conn, evs), 0)  # dedup
        lines = self.paths.events.read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(store.counts(conn)["total"], 2)

    def test_rebuild_from_jsonl(self):
        conn = store.connect(self.paths)
        store.append_events(self.paths, conn, [_ev("a"), _ev("b")])
        conn.close()
        self.paths.db.unlink()
        n = store.rebuild(self.paths)
        self.assertEqual(n, 2)
        conn2 = store.connect(self.paths)
        self.assertEqual(store.counts(conn2)["total"], 2)

    def test_query_range_and_meta_roundtrip(self):
        conn = store.connect(self.paths)
        store.append_events(self.paths, conn, [
            _ev("a", "2026-06-16"), _ev("b", "2026-06-17"), _ev("c", "2026-06-20")])
        rows = store.query_range(conn, "2026-06-16", "2026-06-17")
        self.assertEqual({r["event_id"] for r in rows}, {"a", "b"})
        self.assertEqual(rows[0]["meta"]["prompt_count"], 2)

    def test_archive_copy(self):
        src = Path(self.tmp.name) / "src.jsonl"
        src.write_text("hello")
        dest = store.archive_file(self.paths, "claude", src)
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "hello")
        self.assertEqual(dest.parent, self.paths.claude_archive)


if __name__ == "__main__":
    unittest.main()
