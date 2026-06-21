import unittest

from devlog import engine


class EngineTest(unittest.TestCase):
    def test_missing_engine_returns_none(self):
        self.assertFalse(engine.engine_available("definitely-not-a-real-binary-xyz"))
        self.assertIsNone(engine.run_engine("hi", name="definitely-not-a-real-binary-xyz"))

    def test_available_uses_which(self):
        # 'echo' exists on PATH on Linux; run_engine should return its stdout
        if engine.engine_available("echo"):
            out = engine.run_engine("hello", name="echo")
            self.assertIsNotNone(out)


if __name__ == "__main__":
    unittest.main()
