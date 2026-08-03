import unittest

from core.config import APP_VERSION
from tools.update_release_changelog import RELEASES, entries


class ReleaseMetadataTests(unittest.TestCase):
    def test_release_version_and_changelog_cover_every_new_api(self):
        self.assertEqual("v18.23.26", APP_VERSION)
        with open("CHANGELOG.md", encoding="utf-8-sig") as handle:
            changelog = handle.read()
        self.assertIn("## v18.23.26", changelog)
        for version, modules in RELEASES.items():
            self.assertIn(f"### {version}", changelog)
            for module in modules:
                for feature in entries(module):
                    with self.subTest(version=version, api=feature["api"]):
                        self.assertIn(
                            f"`{feature['id']}` · `{feature['api']}`", changelog
                        )


if __name__ == "__main__":
    unittest.main()
