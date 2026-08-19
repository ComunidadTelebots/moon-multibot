import unittest
from pathlib import Path

from core.security_insights import build_alerts, detect_anomalies, redact_results, search_history, summarize_history


class SecurityInsightsTests(unittest.TestCase):
    def test_intent_search_expands_terms_and_ranks_exact_matches(self):
        rows = [
            {"kind": "image", "source": "vision", "risk": "clean", "filename": "foto.png"},
            {"kind": "url", "source": "virustotal", "risk": "high", "signals": ["phishing", "login"]},
            {"kind": "file", "source": "virustotal", "risk": "high", "filename": "troyano.exe"},
        ]
        results = search_history(rows, "fraude credenciales")
        self.assertEqual(results[0]["kind"], "url")
        self.assertIn("phishing", results[0]["matched_terms"])
        self.assertNotIn("foto.png", [row.get("filename") for row in results])

    def test_summary_is_explainable_and_tolerates_bad_counters(self):
        result = summarize_history([
            {"kind": "url", "source": "vt", "risk": "high", "malicious": "bad", "signals": ["redirect"]},
            {"kind": "file", "source": "vt", "risk": "clean", "malicious": 0},
        ])
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["suspicious"], 1)
        self.assertIn("determinista", result["explanation"])

    def test_anomaly_requires_baseline_and_detects_risk_spike(self):
        self.assertFalse(detect_anomalies([{}] * 10)["ready"])
        baseline = [{"risk": "clean", "source": "vision"} for _ in range(25)]
        recent = [{"risk": "high", "source": "virustotal"} for _ in range(25)]
        result = detect_anomalies(baseline + recent)
        self.assertTrue(result["ready"])
        self.assertIn("risk_spike", [row["code"] for row in result["anomalies"]])

    def test_adaptive_alert_preferences_and_acknowledgement(self):
        rows = [{"risk": "high", "source": "vt"}] * 6
        alerts = build_alerts(rows, {"anomalies": []}, "high", [])
        self.assertEqual(len(alerts), 1)
        self.assertFalse(alerts[0]["acknowledged"])
        acknowledged = build_alerts(rows, {"anomalies": []}, "high", [alerts[0]["id"]])
        self.assertTrue(acknowledged[0]["acknowledged"])
        self.assertEqual(build_alerts(rows, {"anomalies": []}, "critical", []), [])

    def test_privacy_redaction_removes_identifiers_server_side(self):
        source = [{"value": "https://private.example/path", "filename": "secret.exe", "kind": "file"}]
        result = redact_results(source, True)[0]
        self.assertNotIn("value", result)
        self.assertNotIn("filename", result)
        self.assertEqual(len(result["fingerprint"]), 12)
        self.assertEqual(redact_results(source, False)[0]["filename"], "secret.exe")

    def test_endpoint_and_hub_use_existing_components(self):
        root = Path(__file__).parents[1]
        routes = (root / "core" / "routes_security.py").read_text(encoding="utf-8")
        hub = (root / "web" / "hub.html").read_text(encoding="utf-8")
        self.assertEqual(routes.count('/api/security/threat-insights'), 1)
        self.assertEqual(routes.count('/api/security/threat-preferences'), 1)
        self.assertEqual(routes.count('/api/security/threat-alerts/ack'), 1)
        self.assertIn('id="masterThreatSearch"', hub)
        self.assertIn('id="masterThreatPrivacy"', hub)
        self.assertIn('data-threat-ack', hub)
        self.assertIn('class="master-grid"', hub)
        self.assertIn('class="casbox"', hub)


if __name__ == "__main__":
    unittest.main()
