"""Per-ID and security regression tests for future-5162..future-5339."""

import importlib
from unittest import mock
import unittest

import resource_cache_rotation_engines as cache_rotation
import resource_grouped_routing_engines as grouped_routing
from resource_grouped_routing_cache_rotation_manifest import MANIFEST


MASTER = {"id": "master-1", "roles": ["master"], "scopes": []}


def _group_events(index):
    resource, entity_field, kinds = grouped_routing._GROUP_SPECS[index]
    kind = sorted(kinds)[0]
    entity = "https://example.org/item" if entity_field == "normalized_url" else f"{resource}-1"
    base = {
        entity_field: entity, "kind": kind, "severity": "warning",
        "occurred_at": "2026-07-30T10:05:00Z", "title": "Cambio <b>detectado</b>",
        "details": {"token": "must-not-leak"},
    }
    return {**base, "id": f"event-{index}-a"}, {**base, "id": f"event-{index}-b", "severity": "critical", "occurred_at": "2026-07-30T10:10:00Z"}


def _test_group(index):
    def test(self):
        first, second = _group_events(index)
        result = grouped_routing.GROUP_APIS[index]([first, first.copy(), second], actor=MASTER)
        self.assertEqual(result["feature_id"], grouped_routing.IDS[index])
        self.assertEqual(result["unique_count"], 2)
        self.assertEqual(result["notification_count"], 1)
        self.assertEqual(result["notifications"][0]["severity"], "critical")
        self.assertIn("&lt;b&gt;", result["notifications"][0]["titles"][0])
        self.assertEqual(result["planned_by"], MASTER["id"])
        self.assertFalse(result["delivery_requested"])
    return test


def _routing_data(index):
    resource, kind, skill, _ = grouped_routing._ROUTE_SPECS[index]
    item = {"id": f"item-{index}", "kind": kind, "severity": "critical", "region": "ES"}
    destinations = [
        {"id": "busy-target", "skills": [skill], "regions": ["ES"], "clearance": "restricted", "capacity": 2, "load": 2, "active": True},
        {"id": "ready-target", "skills": [skill], "regions": ["ES"], "clearance": "restricted", "capacity": 10, "load": 2, "active": True},
    ]
    return item, destinations


def _test_route(index):
    def test(self):
        item, destinations = _routing_data(index)
        result = grouped_routing.ROUTE_APIS[index](item, destinations, actor=MASTER)
        self.assertEqual(result["feature_id"], grouped_routing.IDS[13 + index])
        self.assertEqual(result["selected_destination"], "ready-target")
        self.assertTrue(result["routable"])
        self.assertFalse(result["dispatched"])
        self.assertFalse(result["executed"])
    return test


def _entry(entity_id, version, value, timestamp="2026-07-30T10:00:00Z"):
    return {
        "id": entity_id, "version": version, "tombstone": False,
        "value": value, "updated_at": timestamp, "etag": cache_rotation.cache_etag(value),
    }


def _test_cache(index):
    def test(self):
        field = sorted(cache_rotation._CACHE_SPECS[index][1])[0]
        cached = _entry(f"entity-{index}", 1, {field: "old"})
        source = _entry(f"entity-{index}", 2, {field: "new"}, "2026-07-30T10:01:00Z")
        result = cache_rotation.CACHE_APIS[index](cached, source, actor=MASTER)
        self.assertEqual(result["feature_id"], cache_rotation.IDS[index])
        self.assertEqual(result["action"], "refresh")
        self.assertEqual(result["selected_version"], 2)
        self.assertFalse(result["applied"])
        self.assertEqual(result["render_mode"], "data_only")
    return test


def _rotation_data(index, healthy=True):
    resource, artifact_field, minimum_grace = cache_rotation._ROTATION_SPECS[index]
    current = {"rotation_key": f"logical-{index}", artifact_field: f"old-{index}", "version": 2, "state": "active", "dependencies": []}
    replacement = {"rotation_key": f"logical-{index}", artifact_field: f"new-{index}", "version": 3, "state": "candidate", "dependencies": [{"id": "dependency-1", "healthy": healthy}]}
    policy = {"grace_minutes": minimum_grace, "batch_size": 5, "health_checks": ["availability", "error_rate"]}
    return current, replacement, policy


def _test_rotation(index):
    def test(self):
        current, replacement, policy = _rotation_data(index)
        result = cache_rotation.ROTATION_APIS[index](current, replacement, policy, actor=MASTER)
        self.assertEqual(result["feature_id"], cache_rotation.IDS[17 + index])
        self.assertTrue(result["safe_to_start"])
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["rollback_until_phase"], 4)
        self.assertEqual(len(result["phases"]), 5)
        self.assertFalse(result["executed"])
    return test


class ResourceGroupedRoutingCacheRotationPerIdTests(unittest.TestCase):
    pass


for _index, _manifest_entry in enumerate(MANIFEST):
    if _index < 13:
        _test = _test_group(_index)
    elif _index < 30:
        _test = _test_route(_index - 13)
    elif _index < 47:
        _test = _test_cache(_index - 30)
    else:
        _test = _test_rotation(_index - 47)
    setattr(ResourceGroupedRoutingCacheRotationPerIdTests, f"test_{_manifest_entry['id'].replace('-', '_')}", _test)


class ResourceGroupedRoutingCacheRotationSecurityTests(unittest.TestCase):
    def test_manifest_complete_and_callable(self):
        self.assertEqual(len(MANIFEST), 60)
        for entry in MANIFEST:
            self.assertEqual(set(entry), {"id", "title", "capability", "module", "api", "test", "preflight", "roles"})
            self.assertIn("master", entry["roles"])
            module = importlib.import_module(entry["module"].removesuffix(".py"))
            self.assertTrue(callable(getattr(module, entry["api"])))

    def test_authorization_is_required(self):
        item, destinations = _routing_data(0)
        viewer = {"id": "viewer-1", "roles": ["viewer"], "scopes": []}
        with self.assertRaises(PermissionError):
            grouped_routing.route_administrative_sessions_intelligently(item, destinations, actor=viewer)
        first, _ = _group_events(0)
        with self.assertRaises(PermissionError):
            grouped_routing.group_editorial_articles_notifications([first], actor=viewer)
        source = _entry("entity-1", 1, {"role": "admin"})
        with self.assertRaises(PermissionError):
            cache_rotation.reconcile_temporary_roles_cache(None, source, actor=viewer)
        current, replacement, policy = _rotation_data(0)
        with self.assertRaises(PermissionError):
            cache_rotation.plan_safe_creator_accounts_rotation(current, replacement, policy, actor=viewer)

    def test_grouped_title_is_escaped_for_telegram_html(self):
        first, _ = _group_events(0)
        result = grouped_routing.group_editorial_articles_notifications([first], actor=MASTER)
        self.assertNotIn("<b>", result["notifications"][0]["titles"][0])
        self.assertIn("&lt;b&gt;", result["notifications"][0]["titles"][0])

    def test_cache_rejects_secrets_and_traversal(self):
        with self.assertRaises(ValueError):
            cache_rotation.cache_etag({"config": {"token": "secret"}})
        source = _entry("../escape", 1, {"role": "admin"})
        with self.assertRaises(ValueError):
            cache_rotation.reconcile_temporary_roles_cache(None, source, actor=MASTER)
        with self.assertRaises(ValueError):
            cache_rotation.cache_etag({"config": {"access_token": "secret"}})
        with self.assertRaises(ValueError):
            cache_rotation.reconcile_temporary_roles_cache(None, _entry("NUL.txt", 1, {"role": "admin"}), actor=MASTER)

    def test_grouped_details_redact_compound_secret_keys(self):
        first, _ = _group_events(0)
        first["details"] = {"nested": {"access_token": "secret", "clientSecret": "secret"}, "status": "ok"}
        result = grouped_routing.group_editorial_articles_notifications([first], actor=MASTER)
        serialized = repr(result)
        self.assertNotIn("access_token", serialized)
        self.assertNotIn("clientSecret", serialized)
        self.assertNotIn("secret", serialized)

    def test_cache_detects_concurrent_same_version_conflict(self):
        cached = _entry("entity-1", 2, {"role": "editor"})
        source = _entry("entity-1", 2, {"role": "admin"})
        result = cache_rotation.reconcile_temporary_roles_cache(cached, source, actor=MASTER)
        self.assertTrue(result["conflict"])
        self.assertEqual(result["action"], "manual_review")
        self.assertFalse(result["applied"])

    def test_unhealthy_rotation_is_blocked_and_never_executes(self):
        current, replacement, policy = _rotation_data(0, healthy=False)
        result = cache_rotation.plan_safe_creator_accounts_rotation(current, replacement, policy, actor=MASTER)
        self.assertFalse(result["safe_to_start"])
        self.assertEqual(result["blockers"], ("dependency-1",))
        self.assertFalse(result["executed"])

    def test_bounded_input_rejects_nonfinite_and_excessive_skills(self):
        item, destinations = _routing_data(0)
        destinations[1]["skills"] = ["session_security"] * 101
        with self.assertRaises(ValueError):
            grouped_routing.route_administrative_sessions_intelligently(item, destinations, actor=MASTER)
        with self.assertRaises(ValueError):
            cache_rotation.cache_etag({"value": float("nan")})

    def test_external_link_grouping_never_performs_network_io(self):
        first, _ = _group_events(12)
        first["normalized_url"] = "https://127.0.0.1/internal"
        with mock.patch("socket.create_connection") as connect:
            result = grouped_routing.group_external_links_notifications([first], actor=MASTER)
        connect.assert_not_called()
        self.assertEqual(result["notification_count"], 1)

    def test_identifier_injection_is_rejected(self):
        item, destinations = _routing_data(0)
        item["id"] = "item;rm"
        with self.assertRaises(ValueError):
            grouped_routing.route_administrative_sessions_intelligently(item, destinations, actor=MASTER)


if __name__ == "__main__":
    unittest.main()
