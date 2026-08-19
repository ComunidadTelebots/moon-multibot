import unittest
from unittest.mock import patch

from flask import Flask

from core import routes_public
from core.hub_release_assets import read_hub_release_asset


class HubReleaseAssetSecurityTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def _request(self, resolved_channel, body):
        user = {"id": "42", "first_name": "Ada"}
        with self.app.test_request_context(
            "/api/public/hub-release-asset", method="POST", json=body
        ), patch.object(routes_public, "_verify_init_data", return_value=user), patch.object(
            routes_public, "_miniapp_release_channel", return_value=resolved_channel
        ):
            return routes_public.hub_release_asset()

    def test_client_cannot_upgrade_its_server_resolved_channel(self):
        response = self._request("stable", {
            "initData": "signed", "release_channel": "alpha", "asset": "manifest"
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual("stable", response.get_json()["channel"])
        self.assertEqual("stable", response.headers["X-Moon-Release-Channel"])
        self.assertEqual("private, no-store", response.headers["Cache-Control"])
        self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])

    def test_unknown_and_traversal_assets_are_not_served(self):
        for asset in ("../alpha.manifest", "alpha", "script.js"):
            response, status = self._request("stable", {"initData": "signed", "asset": asset})
            self.assertEqual(404, status)
            self.assertFalse(response.get_json()["ok"])

    def test_missing_telegram_authentication_fails_closed(self):
        with self.app.test_request_context(
            "/api/public/hub-release-asset", method="POST", json={"asset": "manifest"}
        ), patch.object(routes_public, "_verify_init_data", return_value=None):
            response, status = routes_public.hub_release_asset()
        self.assertEqual(401, status)
        self.assertFalse(response.get_json()["ok"])

    def test_reader_requires_exact_known_channel(self):
        with self.assertRaises(ValueError):
            read_hub_release_asset("unknown", "manifest")
        payload, content_type = read_hub_release_asset("alpha", "manifest")
        self.assertIn(b'"channel":"alpha"', payload)
        self.assertTrue(content_type.startswith("application/json"))


if __name__ == "__main__":
    unittest.main()
