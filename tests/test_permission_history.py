import unittest

from permission_history import record_permission_snapshot


class MemoryDB:
    def __init__(self):
        self.values = {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class FakeBot:
    bot_id = "123"
    bot_username = "TestBot"


class PermissionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()

    def test_identical_checks_do_not_duplicate_events(self):
        missing = [{"permission": "can_delete_messages", "label": "Eliminar mensajes"}]
        first, changed = record_permission_snapshot(
            self.db, "-1001", FakeBot(), "administrator", "supergroup", missing, "42"
        )
        second, changed_again = record_permission_snapshot(
            self.db, "-1001", FakeBot(), "administrator", "supergroup", missing, "42"
        )
        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)

    def test_permission_change_creates_a_new_event(self):
        record_permission_snapshot(
            self.db, "-1001", FakeBot(), "administrator", "supergroup",
            [{"permission": "can_delete_messages", "label": "Eliminar mensajes"}], "42"
        )
        history, changed = record_permission_snapshot(
            self.db, "-1001", FakeBot(), "administrator", "supergroup", [], "42"
        )
        self.assertTrue(changed)
        self.assertEqual(len(history), 2)
        self.assertTrue(history[0]["healthy"])


if __name__ == "__main__":
    unittest.main()
