import unittest
from unittest.mock import patch

from core import channel_stats


class FakePocketBase:
    def __init__(self):
        self.fields = []

    def ensure_collection(self, *_args, **_kwargs):
        return False

    def ensure_field(self, collection, field):
        self.fields.append((collection, field["name"]))
        return False


class AdTemplateSchemaRepairTests(unittest.TestCase):
    def test_existing_template_collection_repairs_every_required_field(self):
        pb = FakePocketBase()
        with patch.object(channel_stats, "_pb", None):
            channel_stats.init(pb)
        repaired = {name for collection, name in pb.fields if collection == channel_stats.C_AD_TEMPLATES}
        self.assertEqual({"chat_id", "name", "text", "image", "target_url", "created_by"}, repaired)


if __name__ == "__main__":
    unittest.main()
