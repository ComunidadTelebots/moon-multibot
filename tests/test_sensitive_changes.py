import unittest

from group_suite import GroupSuite


class MemoryDB:
    def __init__(self):
        self.values = {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class SensitiveChangesTests(unittest.TestCase):
    def setUp(self):
        self.suite = GroupSuite(MemoryDB())

    def test_sensitive_change_records_actor_source_and_difference(self):
        self.suite.save_config(
            "-1001", {"raid": {"enabled": False}}, actor="42", source="telegram-webapp"
        )
        history = self.suite.sensitive_changes("-1001")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["actor"], "42")
        self.assertEqual(history[0]["source"], "telegram-webapp")
        self.assertEqual(history[0]["risk"], "critical")
        self.assertEqual(history[0]["changes"][0]["section"], "raid")

    def test_identical_save_does_not_duplicate_events(self):
        update = {"media_security": {"enabled": True, "action": "delete"}}
        self.suite.save_config("-1001", update, actor="admin", source="web")
        self.suite.save_config("-1001", update, actor="admin", source="web")
        self.assertEqual(len(self.suite.sensitive_changes("-1001")), 1)

    def test_non_sensitive_appearance_change_is_not_recorded(self):
        self.suite.save_config("-1001", {"appearance": {"accent": "violet"}})
        self.assertEqual(self.suite.sensitive_changes("-1001"), [])


if __name__ == "__main__":
    unittest.main()
