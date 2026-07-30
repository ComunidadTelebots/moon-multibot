import unittest

from core import routes_public


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
        self.previous_db = routes_public._db
        routes_public._db = MemoryDB()

    def tearDown(self):
        routes_public._db = self.previous_db

    def test_identical_checks_do_not_duplicate_events(self):
        missing = [{"permission": "can_delete_messages", "label": "Eliminar mensajes"}]
        first, changed = routes_public._record_permission_snapshot(
            "-1001", FakeBot(), "administrator", "supergroup", missing, "42"
        )
        second, changed_again = routes_public._record_permission_snapshot(
            "-1001", FakeBot(), "administrator", "supergroup", missing, "42"
        )
        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)

    def test_permission_change_creates_a_new_event(self):
        routes_public._record_permission_snapshot(
            "-1001", FakeBot(), "administrator", "supergroup",
            [{"permission": "can_delete_messages", "label": "Eliminar mensajes"}], "42"
        )
        history, changed = routes_public._record_permission_snapshot(
            "-1001", FakeBot(), "administrator", "supergroup", [], "42"
        )
        self.assertTrue(changed)
        self.assertEqual(len(history), 2)
        self.assertTrue(history[0]["healthy"])


if __name__ == "__main__":
    unittest.main()
