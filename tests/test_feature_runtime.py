import unittest

from core.feature_runtime import execute, list_features, registry


class FeatureRuntimeTests(unittest.TestCase):
    def test_registry_is_unique_and_callable(self):
        features = list_features()
        self.assertEqual(1920, len(features))
        self.assertEqual(len(features), len({row["id"] for row in features}))
        self.assertTrue(all(callable(row["callable"]) for row in registry().values()))
        self.assertTrue(all(row["minimum_role"] in {"user", "group_admin", "group_creator", "master"} for row in features))
        self.assertEqual({"user", "group_admin", "group_creator", "master"}, {row["minimum_role"] for row in features})

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

    def test_role_filter_and_execution_are_enforced(self):
        user_ids = {row["id"] for row in list_features("user")}
        master_only = next(row for row in list_features() if row["minimum_role"] == "master")
        self.assertNotIn(master_only["id"], user_ids)
        with self.assertRaises(PermissionError):
            execute(master_only["id"], {"args": [], "kwargs": {}}, actor_role="user")


if __name__ == "__main__":
    unittest.main()
