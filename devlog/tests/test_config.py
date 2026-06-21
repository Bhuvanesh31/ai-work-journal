import os
import unittest
from pathlib import Path

from devlog import config


class ConfigTest(unittest.TestCase):
    def test_explicit_root_wins(self):
        p = config.get_paths("/tmp/dl")
        self.assertEqual(p.root, Path("/tmp/dl"))
        self.assertEqual(p.events, Path("/tmp/dl/events.jsonl"))
        self.assertEqual(p.db, Path("/tmp/dl/journal.db"))
        self.assertEqual(p.claude_archive, Path("/tmp/dl/archive/claude"))

    def test_env_root(self):
        os.environ["DEVLOG_ROOT"] = "/tmp/envdl"
        try:
            self.assertEqual(config.resolve_root(), Path("/tmp/envdl"))
        finally:
            del os.environ["DEVLOG_ROOT"]

    def test_ensure_dirs_creates_tree(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = config.get_paths(os.path.join(d, "store"))
            config.ensure_dirs(p)
            self.assertTrue(p.claude_archive.is_dir())
            self.assertTrue(p.codex_archive.is_dir())
            self.assertTrue((p.reports / "daily").is_dir())


if __name__ == "__main__":
    unittest.main()
