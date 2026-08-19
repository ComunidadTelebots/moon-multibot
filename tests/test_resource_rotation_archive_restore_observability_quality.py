"""Per-ID and security tests for Moonbot future-5342..future-5519."""

import importlib
import socket
from unittest import mock
import unittest

import resource_observability_quality_engines as observation
import resource_rotation_archive_restore_engines as lifecycle
from resource_cache_rotation_engines import cache_etag
from resource_rotation_archive_restore_observability_quality_manifest import MANIFEST


MASTER = {"id": "master-1", "roles": ["master"], "scopes": []}
VIEWER = {"id": "viewer-1", "roles": ["viewer"], "scopes": []}


def _rotation_data(index, healthy=True):
    resource, field, grace = lifecycle._ROTATION_SPECS[index]
    current = {"rotation_key": f"logical-{index}", field: f"old-{index}", "version": 2, "state": "active", "dependencies": []}
    replacement = {"rotation_key": f"logical-{index}", field: f"new-{index}", "version": 3, "state": "candidate", "dependencies": [{"id": "dependency-1", "healthy": healthy}]}
    return current, replacement, {"grace_minutes": grace, "batch_size": 5, "health_checks": ["availability"]}


def _test_rotation(index):
    def test(self):
        result = lifecycle.ROTATION_APIS[index](*_rotation_data(index), actor=MASTER)
        self.assertEqual(result["feature_id"], lifecycle.IDS[index])
        self.assertTrue(result["safe_to_start"])
        self.assertTrue(result["requires_approval"])
        self.assertFalse(result["executed"])
    return test


def _archive_data(index, legal_hold=False):
    _, retention, _ = lifecycle._ARCHIVE_SPECS[index]
    records = [{"id": f"record-{index}", "updated_at": "2026-06-01T10:00:00Z", "state": "active", "legal_hold": legal_hold, "size_bytes": 1024, "version": 1}]
    schedule = {"evaluated_at": "2026-07-30T10:00:00Z", "run_at": "2026-07-30T11:00:00Z", "cutoff_before": "2026-07-01T00:00:00Z", "retention_days": retention, "batch_size": 100, "destination_id": "archive-vault-1", "encryption_key_version": 2}
    return records, schedule


def _test_archive(index):
    def test(self):
        result = lifecycle.ARCHIVE_APIS[index](*_archive_data(index), actor=MASTER)
        self.assertEqual(result["feature_id"], lifecycle.IDS[3 + index])
        self.assertEqual(result["eligible_ids"], (f"record-{index}",))
        self.assertTrue(result["manifest_checksum"])
        self.assertFalse(result["delete_source"])
        self.assertFalse(result["executed"])
    return test


def _restore_data(index):
    field = sorted(lifecycle._RESTORE_SPECS[index][1])[0]
    current = {"version": 3, "value": {field: "current"}}
    old = {field: "historical"}
    history = [{"entity_id": f"entity-{index}", "version": 1, "value": old, "tombstone": False, "checksum": cache_etag(old), "valid_from": "2026-01-01T00:00:00Z", "valid_to": "2026-07-01T00:00:00Z"}]
    return f"entity-{index}", current, history, "2026-06-01T00:00:00Z", 3


def _test_restore(index):
    def test(self):
        result = lifecycle.RESTORE_APIS[index](*_restore_data(index), actor=MASTER)
        self.assertEqual(result["feature_id"], lifecycle.IDS[20 + index])
        self.assertTrue(result["restorable"])
        self.assertEqual(result["snapshot_version"], 1)
        self.assertTrue(result["requires_approval"])
        self.assertFalse(result["applied"])
    return test


def _spans(index):
    resource, operations = observation._OBS_SPECS[index]
    first_op, second_op = sorted(operations)[:2]
    return [
        {"trace_id": f"trace-{index}", "span_id": f"root-{index}", "parent_id": None, "node": "api-node", "operation": first_op, "status": "ok", "started_at": "2026-07-30T10:00:00Z", "ended_at": "2026-07-30T10:00:01Z", "attributes": {"attempt": 1}},
        {"trace_id": f"trace-{index}", "span_id": f"child-{index}", "parent_id": f"root-{index}", "node": "worker-node", "operation": second_op, "status": "error", "started_at": "2026-07-30T10:00:00.200Z", "ended_at": "2026-07-30T10:00:00.900Z", "attributes": {"retry": False}},
    ]


def _test_observability(index):
    def test(self):
        result = observation.OBSERVABILITY_APIS[index](_spans(index), actor=MASTER)
        self.assertEqual(result["feature_id"], observation.IDS[index])
        self.assertEqual(result["trace_count"], 1)
        self.assertEqual(result["span_count"], 2)
        self.assertEqual(result["traces"][0]["error_count"], 1)
        self.assertFalse(result["contains_raw_attributes"])
        self.assertFalse(result["network_export_requested"])
    return test


QUALITY_RECORDS = (
    {"id": "session-1", "user_id": "user-1", "state": "active", "started_at": "2026-07-30T10:00:00Z"},
    {"id": "profile-1", "display_name": "Perfil", "visibility": "members", "language": "es"},
    {"id": "community-1", "title": "Comunidad", "member_count": 100, "bot_permissions": {"delete_messages": True}},
    {"id": "ad-1", "title": "Canal oficial", "url": "https://example.org/community", "enabled": True, "approval_status": "approved"},
    {"id": "voice-1", "duration_seconds": 30, "transcript_status": "completed", "consent": True},
    {"id": "file-1", "sha256": "a" * 64, "risk": "low", "scan_status": "clean"},
    {"id": "captcha-1", "user_id": "user-1", "decision": "pass", "score": 0.99},
)


def _test_quality(index):
    def test(self):
        result = observation.QUALITY_APIS[index]([QUALITY_RECORDS[index]], actor=MASTER)
        self.assertEqual(result["feature_id"], observation.IDS[16 + index])
        self.assertEqual(result["quality_score"], 100)
        self.assertTrue(result["passed"])
        self.assertFalse(result["raw_values_exposed"])
        self.assertFalse(result["mutation_requested"])
    return test


class ResourceLifecycleObservabilityQualityPerIdTests(unittest.TestCase):
    pass


for _index, _manifest_entry in enumerate(MANIFEST):
    if _index < 3: _test = _test_rotation(_index)
    elif _index < 20: _test = _test_archive(_index - 3)
    elif _index < 37: _test = _test_restore(_index - 20)
    elif _index < 53: _test = _test_observability(_index - 37)
    else: _test = _test_quality(_index - 53)
    setattr(ResourceLifecycleObservabilityQualityPerIdTests, f"test_{_manifest_entry['id'].replace('-', '_')}", _test)


class ResourceLifecycleObservabilityQualitySecurityTests(unittest.TestCase):
    def test_manifest_complete_roles_and_callable(self):
        self.assertEqual(len(MANIFEST), 60)
        for entry in MANIFEST:
            self.assertEqual(set(entry), {"id", "title", "capability", "module", "api", "test", "preflight", "roles"})
            self.assertIn("master", entry["roles"])
            module = importlib.import_module(entry["module"].removesuffix(".py"))
            self.assertTrue(callable(getattr(module, entry["api"])))

    def test_all_families_require_authorization(self):
        with self.assertRaises(PermissionError): lifecycle.ROTATION_APIS[0](*_rotation_data(0), actor=VIEWER)
        with self.assertRaises(PermissionError): lifecycle.ARCHIVE_APIS[0](*_archive_data(0), actor=VIEWER)
        with self.assertRaises(PermissionError): lifecycle.RESTORE_APIS[0](*_restore_data(0), actor=VIEWER)
        with self.assertRaises(PermissionError): observation.OBSERVABILITY_APIS[0](_spans(0), actor=VIEWER)
        with self.assertRaises(PermissionError): observation.QUALITY_APIS[0]([QUALITY_RECORDS[0]], actor=VIEWER)

    def test_archive_respects_legal_hold_and_never_deletes(self):
        result = lifecycle.ARCHIVE_APIS[0](*_archive_data(0, legal_hold=True), actor=MASTER)
        self.assertEqual(result["eligible_ids"], ())
        self.assertEqual(result["held_ids"], ("record-0",))
        self.assertFalse(result["delete_source"])

    def test_restore_rejects_checksum_and_concurrent_version(self):
        args = list(_restore_data(0)); args[2][0]["checksum"] = "0" * 64
        with self.assertRaises(ValueError): lifecycle.RESTORE_APIS[0](*args, actor=MASTER)
        args = list(_restore_data(0)); args[4] = 2
        with self.assertRaises(ValueError): lifecycle.RESTORE_APIS[0](*args, actor=MASTER)

    def test_observability_rejects_secrets_and_does_not_export_network(self):
        spans = _spans(0); spans[0]["attributes"] = {"token": "secret"}
        with self.assertRaises(ValueError): observation.OBSERVABILITY_APIS[0](spans, actor=MASTER)
        with mock.patch("socket.create_connection") as connect:
            result = observation.OBSERVABILITY_APIS[0](_spans(0), actor=MASTER)
        connect.assert_not_called(); self.assertFalse(result["network_export_requested"])

    def test_quality_flags_private_ssrf_url_without_fetching(self):
        record = dict(QUALITY_RECORDS[3]); record["url"] = "https://127.0.0.1/internal"
        with mock.patch("socket.create_connection") as connect:
            result = observation.review_house_ads_quality([record], actor=MASTER)
        connect.assert_not_called()
        self.assertIn("unsafe_url", result["results"][0]["issues"])

    def test_quality_never_returns_untrusted_html_values(self):
        record = dict(QUALITY_RECORDS[1]); record["display_name"] = "<script>alert(1)</script>"
        result = observation.review_community_profiles_quality([record], actor=MASTER)
        self.assertNotIn("<script>", str(result))
        self.assertFalse(result["raw_values_exposed"])
        record = dict(QUALITY_RECORDS[1]); record["id"] = "<img src=x onerror=alert(1)>"
        result = observation.review_community_profiles_quality([record], actor=MASTER)
        self.assertEqual(result["results"][0]["record_id"], "invalid-at-0")
        self.assertNotIn("<img", str(result))

    def test_archive_rejects_traversal_and_secret_material(self):
        records, schedule = _archive_data(0); records[0]["id"] = "../escape"
        with self.assertRaises(ValueError): lifecycle.ARCHIVE_APIS[0](records, schedule, actor=MASTER)
        records, schedule = _archive_data(0); records[0]["token"] = "secret"
        with self.assertRaises(ValueError): lifecycle.ARCHIVE_APIS[0](records, schedule, actor=MASTER)


if __name__ == "__main__":
    unittest.main()
