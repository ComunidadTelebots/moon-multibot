import unittest

from core import channel_stats


class PocketBaseStub:
    def __init__(self):
        self.record = {"id": "record1", "chat_id": "-1001", "active": True, "ctype": "channel",
                       "listed": False, "directory_status": "unreviewed"}

    @staticmethod
    def esc(value):
        return str(value)

    def first(self, _collection, _filter):
        return dict(self.record)

    def update(self, _collection, _record_id, data):
        self.record.update(data)
        return dict(self.record)

    def list(self, _collection, filter="", **_kwargs):
        if "directory_status='approved'" in filter:
            return [dict(self.record)] if self.record.get("listed") and self.record.get("directory_status") == "approved" else []
        return [dict(self.record)]


class ChannelDirectoryApprovalTests(unittest.TestCase):
    def setUp(self):
        self.previous = channel_stats._pb
        self.pb = PocketBaseStub()
        channel_stats._pb = self.pb

    def tearDown(self):
        channel_stats._pb = self.previous

    def test_request_is_hidden_until_reviewed(self):
        requested = channel_stats.request_listing("-1001", True, "admin1")
        self.assertEqual("pending", requested["directory_status"])
        self.assertFalse(requested["listed"])
        self.assertEqual([], channel_stats.get_channels())

        approved = channel_stats.review_listing("-1001", "approved", "master")
        self.assertEqual("approved", approved["directory_status"])
        self.assertTrue(approved["listed"])
        self.assertEqual(1, len(channel_stats.get_channels()))

    def test_rejection_hides_an_approved_channel(self):
        channel_stats.review_listing("-1001", "approved", "master")
        rejected = channel_stats.review_listing("-1001", "rejected", "reviewer")
        self.assertFalse(rejected["listed"])
        self.assertEqual([], channel_stats.get_channels())


if __name__ == "__main__":
    unittest.main()
