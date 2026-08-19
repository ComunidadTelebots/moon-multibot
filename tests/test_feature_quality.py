import unittest

from core.feature_quality import audit_features
from core.feature_runtime import registry


class FeatureQualityTests(unittest.TestCase):
    def test_every_registered_feature_has_real_code_metadata_and_test(self):
        problems = audit_features(registry().values())
        self.assertEqual([], problems, "\n".join(problems[:100]))


if __name__ == "__main__":
    unittest.main()
