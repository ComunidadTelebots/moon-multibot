import datetime as dt
import unittest

from community_members import CommunityMembers
from group_suite import GroupSuite


class MemoryDB:
    def __init__(self): self.values = {}
    def get(self, key, default=None): return self.values.get(key, default)
    def set(self, key, value): self.values[key] = value


class IntegratedQuietReminderTests(unittest.TestCase):
    def test_quiet_hours_migrates_legacy_and_saves_canonical_audit(self):
        db = MemoryDB()
        db.set("QUIET_HOURS_-1", {"enabled": True, "start": "22:00", "end": "06:00", "timezone": "group"})
        suite = GroupSuite(db)
        self.assertEqual(suite.config(-1)["quiet_hours"]["timezone"], "Europe/Madrid")
        saved = suite.save_config(-1, {"quiet_hours": {"start": "23:00", "allowed_categories": ["security"]}}, actor="7", source="test")
        self.assertEqual(saved["quiet_hours"]["start"], "23:00")
        self.assertIn("quiet_hours", db.get("GROUPSUITE_-1"))
        self.assertTrue(suite.sensitive_changes(-1))
        self.assertIn("quiet_hours_decision", suite.snapshot(-1))

    def test_persistent_reminder_coexists_and_is_idempotent(self):
        db = MemoryDB(); manager = CommunityMembers(db)
        now = dt.datetime.now(dt.timezone.utc)
        local = (now + dt.timedelta(minutes=2)).astimezone(dt.timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
        item = manager.persistent_reminder("9", "prueba", local.isoformat(timespec="minutes"), "Etc/UTC", "daily")
        self.assertEqual(db.get("COMMUNITY_REMINDERS", []), [])
        self.assertEqual(manager.reminders("9")[0]["id"], item["id"])
        due_at = dt.datetime.fromisoformat(item["next_run"].replace("Z", "+00:00"))
        first = manager.due_persistent_reminders(due_at)
        second = manager.due_persistent_reminders(due_at)
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertIsNotNone(manager.snooze_persistent_reminder("9", item["id"], 10))
        self.assertIsNone(manager.cancel_persistent_reminder("10", item["id"]))
        self.assertIsNotNone(manager.cancel_persistent_reminder("9", item["id"]))

    def test_legacy_aware_datetime_no_longer_raises(self):
        db = MemoryDB(); manager = CommunityMembers(db)
        future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
        self.assertEqual(manager.reminder("1", "legado", future)["status"], "pending")


if __name__ == "__main__": unittest.main()
