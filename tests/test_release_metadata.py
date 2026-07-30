import unittest

from core.config import APP_VERSION
from webapp_proxy_dashboard_analytics_operations_manifest import FEATURES as FIRST_RELEASE_FEATURES
from webapp_analytics_privacy_seo_operations_manifest import FEATURES as SECOND_RELEASE_FEATURES


class ReleaseMetadataTests(unittest.TestCase):
    def test_release_version_and_changelog_cover_every_new_api(self):
        self.assertEqual("v18.23.0", APP_VERSION)
        with open("CHANGELOG.md", encoding="utf-8-sig") as handle:
            changelog = handle.read()
        self.assertIn("## v18.23.0", changelog)
        for feature in (*FIRST_RELEASE_FEATURES, *SECOND_RELEASE_FEATURES):
            with self.subTest(api=feature["api"]):
                self.assertIn(f"`{feature['api']}`", changelog)


if __name__ == "__main__":
    unittest.main()
