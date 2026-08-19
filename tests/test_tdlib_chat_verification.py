import unittest

from core.tdlib_client import TDLibClient


class TDLibChatVerificationTests(unittest.TestCase):
    def client(self, responses):
        client = TDLibClient.__new__(TDLibClient)
        client._auth_state = "authorizationStateReady"
        client.send_await = lambda query, timeout=10: responses.pop(0)
        return client

    def test_reads_official_verified_flag_from_supergroup(self):
        client = self.client([
            {"@type": "chat", "id": -1001, "type": {"@type": "chatTypeSupergroup", "supergroup_id": 77}},
            {"@type": "supergroup", "id": 77, "verification_status": {"@type": "verificationStatus", "is_verified": True}},
        ])
        result = client.get_chat_verification("https://t.me/example")
        self.assertTrue(result["checked"])
        self.assertTrue(result["verified"])
        self.assertEqual("verified", result["status"])

    def test_network_failure_is_unknown_not_unverified(self):
        client = self.client([None])
        result = client.get_chat_verification("@example")
        self.assertFalse(result["checked"])
        self.assertIsNone(result["verified"])
        self.assertEqual("chat_unavailable", result["status"])


if __name__ == "__main__":
    unittest.main()
