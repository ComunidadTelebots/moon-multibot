import unittest

from core.feature_access import can_access_release, normalize_release_channel
from core.feature_runtime import execute, list_features


class FeatureReleaseChannelTests(unittest.TestCase):
    def test_channels_are_progressive_and_invalid_values_fail_to_stable(self):
        feature = {"release_channel": "beta"}
        self.assertFalse(can_access_release(feature, "stable"))
        self.assertFalse(can_access_release(feature, "rc"))
        self.assertTrue(can_access_release(feature, "beta"))
        self.assertTrue(can_access_release(feature, "alpha"))
        self.assertEqual("stable", normalize_release_channel("unknown"))

    def test_alpha_registry_features_are_hidden_from_lower_channels(self):
        stable = {item["id"] for item in list_features("master", "stable")}
        alpha = {item["id"] for item in list_features("master", "alpha")}
        self.assertNotIn("future-2665", stable)
        self.assertIn("future-2665", alpha)

    def test_execution_rechecks_channel(self):
        with self.assertRaises(PermissionError):
            execute("future-2665", {"args": [[]], "kwargs": {}}, "master", "stable")


if __name__ == "__main__":
    unittest.main()
