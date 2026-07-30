import json
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from core import routes_public
from core.config import APP_VERSION


ROOT = Path(__file__).parents[1]


class HubReleaseIdentityTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_tg_auth_uses_server_resolved_channel_and_running_version(self):
        user = {"id": 42, "first_name": "Ada", "username": "ada"}
        with self.app.test_request_context(
            "/api/public/tg_auth",
            method="POST",
            json={"initData": "signed", "release_channel": "alpha"},
        ), patch.object(routes_public, "_verify_init_data", return_value=user), patch.object(
            routes_public, "_miniapp_release_channel", return_value="rc"
        ), patch.object(routes_public, "_master_id", "999"), patch.object(
            routes_public, "_jwt_secret", None
        ):
            response = routes_public.tg_auth()
        payload = response.get_json()
        self.assertEqual("rc", payload["release_channel"])
        self.assertEqual(APP_VERSION, payload["app_version"])
        self.assertFalse(payload["is_master"])

    def test_all_channel_manifests_are_data_only_and_consistent(self):
        for channel in ("stable", "rc", "beta", "alpha"):
            path = ROOT / "web" / "hub-channels" / f"{channel}.manifest"
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, payload["schema_version"])
            self.assertEqual(channel, payload["channel"])
            self.assertIsInstance(payload["isolated_assets"], list)

    def test_hub_displays_identity_and_only_loads_allowlisted_manifest(self):
        source = (ROOT / "web" / "hub.html").read_text(encoding="utf-8")
        self.assertIn('new Set(["stable","rc","beta","alpha"])', source)
        self.assertIn('applyHubReleaseIdentity(d.release_channel,d.app_version)', source)
        self.assertIn('fetch(`/hub-channels/${channel}.manifest`', source)
        self.assertIn('bundle.channel!==channel||bundle.schema_version!==1', source)
        self.assertIn('id="releaseBadge"', source)
        self.assertIn('id="classicRelease"', source)


if __name__ == "__main__":
    unittest.main()
