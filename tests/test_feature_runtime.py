import unittest

from core.feature_runtime import execute, list_features, registry


class FeatureRuntimeTests(unittest.TestCase):
    def test_registry_is_unique_and_callable(self):
        features = list_features()
        self.assertEqual(1240, len(features))
        self.assertEqual(len(features), len({row["id"] for row in features}))
        self.assertTrue(all(callable(row["callable"]) for row in registry().values()))

    def test_executes_only_registered_function(self):
        result = execute("future-3002", {
            "args": [[{"active_roles": 2, "expiring_roles": 1},
                      {"active_roles": 4, "expiring_roles": 1}]],
            "kwargs": {"horizon": 2, "slot_capacity": 10},
        })
        self.assertEqual("future-3002", result["feature_id"])
        with self.assertRaises(KeyError):
            execute("os.system", {"args": ["whoami"]})

    def test_rejects_unbound_or_malformed_payload(self):
        with self.assertRaises((TypeError, ValueError)):
            execute("future-3002", {"kwargs": {}})
        with self.assertRaises(ValueError):
            execute("future-3002", [])


if __name__ == "__main__":
    unittest.main()
