import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.proxy_manager import ProxyManager


ROOT = Path(__file__).resolve().parents[1]


class MemoryDb:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class DeepSecurityHardeningTests(unittest.TestCase):
    def test_proxy_ports_reject_remote_shell_metacharacters(self):
        manager = ProxyManager(MemoryDb())
        with self.assertRaises(ValueError):
            manager.save_vps_config({"ports": ["443; id"]})
        with self.assertRaises(ValueError):
            manager.save_vps_config({"ports": [70000]})

    @patch("core.proxy_manager.paramiko.SSHClient")
    def test_ssh_rejects_unknown_host_keys(self, ssh_client):
        client = Mock()
        ssh_client.return_value = client
        manager = ProxyManager(MemoryDb({"PROXY_VPS_CONFIG": {"host": "vps.example", "ports": [443]}}))
        client.exec_command.return_value = (Mock(), Mock(), Mock())
        client.exec_command.return_value[1].read.return_value = b""
        client.exec_command.return_value[2].read.return_value = b""
        manager.ssh_exec("true")
        client.load_system_host_keys.assert_called_once_with()
        policy = client.set_missing_host_key_policy.call_args.args[0]
        self.assertEqual(policy.__class__.__name__, "RejectPolicy")

    def test_plugins_never_deserialize_pickle_at_import(self):
        source = (ROOT / "plugins" / "moderation_advanced.py").read_text(encoding="utf-8")
        self.assertNotIn("pickle.load", source)
        self.assertNotIn("pickle.loads", source)

    def test_restore_command_rejects_path_traversal(self):
        source = (ROOT / "plugins" / "backup_utils.py").read_text(encoding="utf-8")
        self.assertIn("os.path.commonpath", source)
        self.assertIn("re.fullmatch", source)
        restore_source = source.split('elif t_lower.startswith("/restore_db"):', 1)[1]
        self.assertNotIn('open(f"data/{filename}"', restore_source)

    def test_jwt_is_never_accepted_or_rendered_in_query_strings(self):
        server = (ROOT / "moon_multibot.py").read_text(encoding="utf-8")
        dashboard = (ROOT / "web" / "script.js").read_text(encoding="utf-8")
        legacy_dashboard = (ROOT / "web" / "script_clean.js").read_text(encoding="utf-8")
        self.assertNotIn('req.args.get("token")', server)
        self.assertNotIn("/api/ia/download?token=", dashboard)
        self.assertNotIn("/api/logs/download?token=", legacy_dashboard)

    def test_dashboard_login_has_brute_force_protection(self):
        server = (ROOT / "moon_multibot.py").read_text(encoding="utf-8")
        login_source = server.split('@app.route("/api/login"', 1)[1].split('@app.route("/health"', 1)[0]
        self.assertIn("_login_rate_limited", login_source)
        self.assertIn("_record_login_failure", login_source)
        self.assertIn("Retry-After", login_source)
        self.assertIn("429", login_source)


if __name__ == "__main__":
    unittest.main()
