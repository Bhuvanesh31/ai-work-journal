import os
import time
import unittest

from devlog import events


class EventHelpersTest(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()

    def test_event_ids_are_stable_and_distinct(self):
        a = events.make_session_event_id("claude", "sess-1", "2026-06-17")
        b = events.make_session_event_id("claude", "sess-1", "2026-06-17")
        c = events.make_session_event_id("claude", "sess-1", "2026-06-18")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(a), 40)  # sha1 hex

    def test_commit_id_stable(self):
        a = events.make_commit_event_id("/repo", "abc123")
        b = events.make_commit_event_id("/repo", "abc123")
        self.assertEqual(a, b)

    def test_derive_project_from_cwd_not_folder(self):
        self.assertEqual(
            events.derive_project("/home/bhuvanesh/leadle_master_claude"),
            "leadle-master-claude",
        )
        self.assertEqual(events.derive_project("/home/x/My Project/"), "my-project")

    def test_to_local_date_handles_utc_z(self):
        # 23:30 UTC on the 17th is still the 17th in UTC tz
        self.assertEqual(events.to_local_date("2026-06-17T23:30:00.000Z"), "2026-06-17")

    def test_parse_ts_is_aware(self):
        dt = events.parse_ts("2026-06-17T23:30:00+05:30")
        self.assertIsNotNone(dt.tzinfo)


if __name__ == "__main__":
    unittest.main()
