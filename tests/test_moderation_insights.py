import hashlib
import hmac
import json
import unittest
from pathlib import Path

from core.moderation_insights import build_snapshot, compare_snapshots, diagnose, signed_export


class ModerationInsightsTests(unittest.TestCase):
    def test_snapshot_comparison_and_adaptive_diagnostics(self):
        previous = build_snapshot({"config": {"raid": {"enabled": True}}, "reports": [],
                                   "consensus": [], "quarantine": {}, "raid": {"active": False}},
                                  {"1": 1}, {"users": []}, [])
        current = build_snapshot({"config": {"raid": {"enabled": True}},
                                  "reports": [{"status": "pending"}] * 5,
                                  "consensus": [{"status": "pending"}],
                                  "quarantine": {"2": {}}, "raid": {"active": True}},
                                 {"1": 7}, {"users": ["2"]}, [{}] * 12)
        comparison = compare_snapshots(previous, current)
        result = diagnose(current, comparison)
        self.assertEqual(comparison["delta"]["spam_events"], 12)
        self.assertTrue(comparison["raid_changed"])
        self.assertFalse(result["healthy"])
        self.assertEqual(result["alerts"][0]["code"], "raid_active")
        self.assertIn("spam_spike", [row["code"] for row in result["alerts"]])

    def test_export_signature_covers_canonical_payload(self):
        result = signed_export("-1001", [{"captured_at": "x", "local_bans": 2}], "secret")
        canonical = json.dumps(result["payload"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        key = hashlib.sha256(b"secret:moderation-export").digest()
        expected = hmac.new(key, canonical.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(result["signature"], expected)
        self.assertEqual(result["algorithm"], "HMAC-SHA256")

    def test_route_and_existing_hub_design_are_integrated(self):
        root = Path(__file__).parents[1]
        routes = (root / "core" / "routes_public.py").read_text(encoding="utf-8")
        hub = (root / "web" / "hub.html").read_text(encoding="utf-8")
        self.assertIn('/api/public/group/moderation/insights', routes)
        self.assertIn('class="dropdown"', hub)
        self.assertIn('id="mInsights"', hub)
        self.assertIn('moderacion-firmada-', hub)


if __name__ == "__main__":
    unittest.main()
