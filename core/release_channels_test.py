import unittest
from core.release_channels import assign, revoke


class FakePB:
    def __init__(self): self.row = None
    @staticmethod
    def esc(value): return str(value)
    def first(self, collection, filter): return self.row
    def upsert(self, collection, filter, data): self.row = {"id": "one", **data}; return self.row
    def update(self, collection, record_id, data): self.row.update(data); return self.row


class ReleaseChannelsTest(unittest.TestCase):
    def test_assign_and_revoke(self):
        pb = FakePB()
        row = assign(pb, "12345", "beta", display_name="Ada", assigned_by="1")
        self.assertEqual(row["release_channel"], "beta")
        self.assertTrue(row["enabled"])
        self.assertTrue(revoke(pb, "12345"))
        self.assertFalse(pb.row["enabled"])

    def test_rejects_invalid_values(self):
        with self.assertRaises(ValueError): assign(FakePB(), "abc", "beta")
        with self.assertRaises(ValueError): assign(FakePB(), "123", "nightly")


if __name__ == "__main__": unittest.main()
