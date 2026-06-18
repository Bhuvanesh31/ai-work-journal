import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from devlog.parsers import gitlog


class GitLogParserTest(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        env = {**os.environ,
               "GIT_AUTHOR_NAME": "Tester", "GIT_AUTHOR_EMAIL": "t@e.x",
               "GIT_COMMITTER_NAME": "Tester", "GIT_COMMITTER_EMAIL": "t@e.x",
               "GIT_AUTHOR_DATE": "2026-06-17T12:00:00+00:00",
               "GIT_COMMITTER_DATE": "2026-06-17T12:00:00+00:00"}
        run = lambda *a: subprocess.run(["git", "-C", str(self.repo), *a],
                                        check=True, capture_output=True, env=env)
        run("init", "-q")
        (self.repo / "f.txt").write_text("hi")
        run("add", ".")
        run("commit", "-q", "-m", "First | commit with pipe")

    def tearDown(self):
        self.tmp.cleanup()

    def test_parses_commit_with_delimiter_safe_subject(self):
        res = gitlog.parse_git_log(self.repo)
        self.assertEqual(len(res.events), 1)
        e = res.events[0]
        self.assertEqual(e["kind"], "commit")
        self.assertEqual(e["summary"], "First | commit with pipe")
        self.assertEqual(e["date"], "2026-06-17")
        self.assertEqual(e["meta"]["author"], "Tester")
        self.assertEqual(len(e["meta"]["commit"]), 40)

    def test_missing_repo_returns_empty(self):
        res = gitlog.parse_git_log("/no/such/repo")
        self.assertEqual(res.events, [])

    def test_toplevel(self):
        self.assertEqual(Path(gitlog.repo_toplevel(self.repo)).resolve(),
                         self.repo.resolve())
        self.assertIsNone(gitlog.repo_toplevel("/no/such/repo"))


if __name__ == "__main__":
    unittest.main()
