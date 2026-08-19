import os
import unittest
from pathlib import Path
from unittest.mock import patch

from core.web_admin_verification import confirm_web_admin


class _Response:
    status_code = 200
    def json(self):
        return {"ok": True, "role": "admin"}


class _Session:
    def __init__(self): self.call = None
    def post(self, url, **kwargs): self.call = (url, kwargs); return _Response()


class WebAdminVerificationTests(unittest.TestCase):
    def test_posts_verified_telegram_identity_to_internal_api(self):
        session = _Session()
        with patch.dict(os.environ, {"MOON_ADMIN_API_KEY": "k" * 32,
                    "WEB_ADMIN_VERIFY_URL": "http://todosobrealltech-api:3001/confirm"}, clear=False):
            result = confirm_web_admin("WEB-ABCDEFGHIJKL", 163103382, "Cuenta_123", session=session)
        self.assertTrue(result["ok"])
        self.assertEqual("163103382", session.call[1]["json"]["telegram_id"])
        self.assertEqual("k" * 32, session.call[1]["headers"]["X-Moon-Admin-Key"])

    def test_rejects_bad_codes_and_untrusted_plain_http_hosts(self):
        with self.assertRaises(ValueError): confirm_web_admin("bad", 12345)
        with patch.dict(os.environ, {"MOON_ADMIN_API_KEY": "k" * 32,
                    "WEB_ADMIN_VERIFY_URL": "http://example.com/confirm"}, clear=False):
            with self.assertRaises(RuntimeError):
                confirm_web_admin("WEB-ABCDEFGHIJKL", 163103382)

    def test_hub_exposes_a_separate_web_admin_surface(self):
        source = Path("web/hub.html").read_text(encoding="utf-8")
        routes = Path("core/routes_public.py").read_text(encoding="utf-8")
        self.assertIn('id="webAdminTab"', source)
        self.assertIn("is_web_admin", routes)
        self.assertIn("telegram_id=", routes)
        self.assertNotIn("miniapp_web_admin", routes)

    def test_command_is_private_and_redacted_from_chat_history(self):
        source = Path("moon_multibot.py").read_text(encoding="utf-8-sig")
        self.assertIn('msg.get("chat", {}).get("type") != "private"', source)
        self.assertIn('/verificarweb [OCULTO]', source)


if __name__ == "__main__":
    unittest.main()
