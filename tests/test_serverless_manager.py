import json
import tempfile
import unittest
from pathlib import Path

from core.serverless_manager import ServerlessError, ServerlessManager
from core.serverless_bridge import ServerlessBridgeStore


def build_manager(tmp_path, runner_output=None):
    project = tmp_path / "cintiaandrea_bot"
    project.mkdir()
    (project / "tgcloud.jsonc").write_text("{}", encoding="utf-8")
    credentials = project / ".tgcloud"
    credentials.mkdir()
    (credentials / "credentials").write_text("never-read", encoding="utf-8")
    registry = tmp_path / "bots.json"
    registry.write_text(json.dumps([{
        "id": "cintiaandrea",
        "name": "Cintia Andrea",
        "app_id": "5724481351",
        "project_dir": "cintiaandrea_bot",
        "stats_endpoint": "moonStats",
    }]), encoding="utf-8")
    manager = ServerlessManager(tmp_path, registry, enabled=True)
    if runner_output is not None:
        manager._run = lambda _project, _args, timeout=None: runner_output
    return manager


class ServerlessManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stats_parses_json_string_from_cli(self):
        manager = build_manager(
            self.root,
            (0, '< \'{"totals":{"users":3,"messages":8},"daily":[]}\'  9ms'),
        )

        self.assertEqual(manager.stats("cintiaandrea")["totals"], {"users": 3, "messages": 8})

    def test_actions_are_allowlisted(self):
        manager = build_manager(self.root, (0, ""))

        with self.assertRaisesRegex(ServerlessError, "no permitida"):
            manager.action("cintiaandrea", "run-any-command")

    def test_project_cannot_escape_registered_root(self):
        registry = self.root / "bots.json"
        registry.write_text(json.dumps([{
            "id": "escape",
            "project_dir": "../outside",
        }]), encoding="utf-8")
        manager = ServerlessManager(self.root, registry, enabled=True)

        with self.assertRaisesRegex(ServerlessError, "no disponible"):
            manager.status("escape")

    def test_tokens_are_redacted(self):
        token = f"{123456789}:{'a' * 30}"
        output = ServerlessManager._redact(f"token {token}")

        self.assertNotIn(token, output)

    def test_bridge_commands_are_allowlisted(self):
        manager = build_manager(self.root, (0, '< \'{"ok":true}\'  4ms'))

        result = manager.bridge_command("cintiaandrea", {
            "action": "send_message", "chatId": -1001, "text": "Hola",
        })
        self.assertTrue(result["ok"])
        with self.assertRaisesRegex(ServerlessError, "no permitida"):
            manager.bridge_command("cintiaandrea", {"action": "run_code"})

    def test_bridge_authentication_is_bot_specific(self):
        secret = ServerlessBridgeStore.secret("jwt-secret", "5724481351")

        self.assertTrue(ServerlessBridgeStore.authenticate(
            f"Bearer {secret}", "jwt-secret", "5724481351"
        ))
        self.assertFalse(ServerlessBridgeStore.authenticate(
            f"Bearer {secret}", "jwt-secret", "999"
        ))

    def test_bridge_store_limits_message_fields(self):
        store = ServerlessBridgeStore(max_events=2)
        snapshot = store.ingest("cintiaandrea", {
            "event": {"chatId": -1, "messageId": 4, "body": "x" * 3000},
            "stats": {"totals": {"messages": 1}},
        })

        self.assertEqual(len(snapshot["events"][0]["body"]), 2000)
        self.assertEqual(snapshot["stats"]["totals"]["messages"], 1)


if __name__ == "__main__":
    unittest.main()
