import unittest

from core.auth_security import dashboard_password_matches


class DashboardAuthSecurityTests(unittest.TestCase):
    def test_valid_configured_credentials_match(self):
        self.assertTrue(dashboard_password_matches("strong-password", "strong-password", "jwt-secret"))

    def test_missing_server_secrets_fail_closed(self):
        self.assertFalse(dashboard_password_matches("", "", ""))
        self.assertFalse(dashboard_password_matches("strong-password", "strong-password", ""))

    def test_missing_or_wrong_client_password_is_rejected(self):
        self.assertFalse(dashboard_password_matches("strong-password", None, "jwt-secret"))
        self.assertFalse(dashboard_password_matches("strong-password", "wrong", "jwt-secret"))
