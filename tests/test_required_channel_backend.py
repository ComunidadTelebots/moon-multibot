import ast
import datetime
import hashlib
import json
import pathlib
import re
import types
import unittest


SOURCE = pathlib.Path("core/routes_public.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def load_functions(*names, namespace=None):
    selected = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in names]
    scope = dict(namespace or {})
    exec(compile(ast.Module(body=selected, type_ignores=[]), "routes_public.py", "exec"), scope)
    return scope


class FakeDb:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.set_calls = 0

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.set_calls += 1
        self.values[key] = value


class RequiredChannelBackendTests(unittest.TestCase):
    def test_bot_identity_uses_id_and_username(self):
        scope = load_functions("_bot_identity_keys")
        keys = scope["_bot_identity_keys"]({"id": 123, "username": "@ExampleBot"})
        self.assertEqual(keys, {"123", "examplebot"})

    def test_group_channel_filter_matches_username_when_group_also_has_id(self):
        rows = [
            {"id": "-1001", "chat_id": "-1001", "ctype": "supergroup",
             "name": "Grupo", "bots": [{"id": "123", "username": "ExampleBot"}]},
            {"id": "-1002", "chat_id": "-1002", "ctype": "channel",
             "name": "Canal", "username": "CanalSeguro", "bots": [{"username": "ExampleBot"}]},
        ]
        bot = types.SimpleNamespace(bot_id="123", bot_username="ExampleBot")
        scope = load_functions(
            "_bot_identity_keys", "_required_channel_suggestions",
            namespace={"_admin_group_rows": lambda: rows, "_get_active_bots": lambda: [bot],
                       "_channel_candidate_review": lambda row: {"eligible": True}},
        )
        suggestions = scope["_required_channel_suggestions"]("-1001")
        self.assertEqual([item["channel"] for item in suggestions], ["CanalSeguro"])
        self.assertTrue(suggestions[0]["bot_joined"])

    def test_content_review_cache_is_reused_until_history_changes(self):
        db = FakeDb({"CHAT_HIST_-1002": [{"message_id": 1, "time": 1, "text": "noticia segura"}]})
        scope = load_functions(
            "_channel_candidate_review",
            namespace={"_db": db, "_safe_list": lambda value: value if isinstance(value, list) else [],
                       "hashlib": hashlib, "json": json, "datetime": datetime, "re": re},
        )
        review = scope["_channel_candidate_review"]({"id": "-1002"})
        cached = scope["_channel_candidate_review"]({"id": "-1002"})
        self.assertEqual(review, cached)
        self.assertEqual(db.set_calls, 1)

        db.values["CHAT_HIST_-1002"].append({"message_id": 2, "time": 2, "text": "otra noticia"})
        updated = scope["_channel_candidate_review"]({"id": "-1002"})
        self.assertNotEqual(review["history_fingerprint"], updated["history_fingerprint"])
        self.assertEqual(db.set_calls, 2)

    def test_invalid_enabled_update_does_not_write_partial_channels(self):
        db = FakeDb({"JOIN_GLOBAL_REQUIRED_CHANNELS": ["CanalActual"],
                     "JOIN_GLOBAL_REQUIRED_ENABLED": True})
        scope = load_functions(
            "_normalize_required_channels", "_global_join_update_candidate",
            namespace={"_db": db},
        )
        channels, enabled, error = scope["_global_join_update_candidate"](
            {"channels": [], "enabled": True}
        )
        self.assertIsNone(channels)
        self.assertIsNone(enabled)
        self.assertEqual(error, "configura al menos un canal")
        self.assertEqual(db.values["JOIN_GLOBAL_REQUIRED_CHANNELS"], ["CanalActual"])
        self.assertEqual(db.set_calls, 0)

    def test_v4_migration_preserves_an_existing_multichannel_list(self):
        db = FakeDb({"JOIN_GLOBAL_DEFAULTS_V3": True,
                     "JOIN_GLOBAL_REQUIRED_CHANNEL": "CanalAntiguo",
                     "JOIN_GLOBAL_REQUIRED_CHANNELS": ["CanalUno", "CanalDos"]})
        scope = load_functions(
            "_normalize_required_channels", "_ensure_global_join_defaults",
            namespace={"_db": db},
        )
        scope["_ensure_global_join_defaults"]()
        self.assertEqual(db.values["JOIN_GLOBAL_REQUIRED_CHANNELS"], ["CanalUno", "CanalDos"])
        self.assertTrue(db.values["JOIN_GLOBAL_DEFAULTS_V4"])


if __name__ == "__main__":
    unittest.main()
