import tempfile
import unittest
from pathlib import Path

from devlog import config, state


class StateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paths = config.get_paths(self.tmp.name)
        config.ensure_dirs(self.paths)
        self.f = Path(self.tmp.name) / "data.jsonl"
        self.f.write_text("one\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_unchanged_after_mark(self):
        st = {}
        self.assertFalse(state.is_unchanged(st, self.f))
        state.mark(st, self.f)
        self.assertTrue(state.is_unchanged(st, self.f))

    def test_change_detected_on_append(self):
        st = {}
        state.mark(st, self.f)
        self.f.write_text("one\ntwo\n")
        self.assertFalse(state.is_unchanged(st, self.f))

    def test_roundtrip_persist(self):
        st = {}
        state.mark(st, self.f)
        state.save_state(self.paths, st)
        loaded = state.load_state(self.paths)
        self.assertTrue(state.is_unchanged(loaded, self.f))


if __name__ == "__main__":
    unittest.main()
