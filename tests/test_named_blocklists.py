import tempfile
import unittest
from pathlib import Path

from ban_manager import BanManager


class MemoryDB:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


class NamedBlocklistsTests(unittest.TestCase):
    def test_multiple_lists_are_independent_and_global_by_default(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "first.txt"
            second = Path(folder) / "second.txt"
            first.write_text("# first\n11111\n22222\n", encoding="utf-8")
            second.write_text("22222\n33333\n", encoding="utf-8")

            class TestManager(BanManager):
                STATIC_BAN_FILES = {
                    "telegram_legacy": first,
                    "telegram_2018_03_09": second,
                }

            manager = TestManager(MemoryDB())
            self.assertEqual(manager.static_bans, {"11111", "22222", "33333"})
            self.assertTrue(manager.is_global_banned("11111"))
            self.assertTrue(manager.is_global_banned("33333"))
            lists = {row["id"]: row for row in manager.get_named_lists()}
            self.assertEqual(lists["telegram_legacy"]["count"], 2)
            self.assertEqual(lists["telegram_2018_03_09"]["count"], 2)
            self.assertEqual(lists["telegram_2018_03_09"]["list_date"], "2018-03-09")

            # Los GBAN creados en ejecución se suman a ambas listas; no las sustituyen.
            self.assertTrue(manager.ban_user("44444", reason="prueba", source="manual"))
            self.assertTrue(manager.is_global_banned("44444"))
            combined = set(manager.get_all_bans()["users"])
            self.assertTrue({"11111", "22222", "33333", "44444"}.issubset(combined))

            manager.configure_named_list("telegram_2018_03_09", enabled=False)
            self.assertFalse(manager.is_global_banned("33333"))
            self.assertTrue(manager.is_global_banned("11111"))

    def test_report_analysis_requires_strong_evidence_and_keeps_master_review(self):
        class TestManager(BanManager):
            STATIC_BAN_FILES = {}

        manager = TestManager(MemoryDB())
        first = manager.create_ban_report("90001", "spam", "admin-1", "group-1", evidence=["mensaje 1"])
        first = manager.analyze_ban_report(first["id"], spam_result={"score": 40, "reasons": []})
        self.assertFalse(first["analysis"]["automatic_eligible"])
        self.assertFalse(manager.is_global_banned("90001"))

        manager.create_ban_report("90001", "spam repetido", "admin-2", "group-2")
        third = manager.create_ban_report("90001", "fraude repetido", "admin-3", "group-3")
        third = manager.analyze_ban_report(third["id"], spam_result={"score": 20, "reasons": []})
        self.assertTrue(third["analysis"]["automatic_eligible"])
        self.assertEqual(third["analysis"]["engine"], "moon_gban_intelligence_v2")
        self.assertGreaterEqual(third["analysis"]["confidence"], 0.7)
        self.assertTrue(third["auto_ban_applied"])
        self.assertTrue(manager.is_global_banned("90001"))
        self.assertEqual(third["status"], "pending")
        self.assertIsNotNone(third["auto_ban_expires_at"])

    def test_cas_match_triggers_temporary_reviewable_ban(self):
        class TestManager(BanManager):
            STATIC_BAN_FILES = {}

        manager = TestManager(MemoryDB())
        report = manager.create_ban_report("90002", "posible spam", "admin", "group")
        report = manager.analyze_ban_report(
            report["id"], spam_result={"score": 0}, cas_result={"ok": True, "banned": True}
        )
        self.assertEqual(report["analysis"]["score"], 100)
        self.assertTrue(report["auto_ban_applied"])

    def test_master_decisions_train_reporter_reliability(self):
        class TestManager(BanManager):
            STATIC_BAN_FILES = {}

        db = MemoryDB()
        manager = TestManager(db)
        report = manager.create_ban_report("90003", "fraude", "admin-trusted", "group")
        manager.resolve_ban_report(report["id"], "approved", "master")
        profile = manager.gban_intelligence.reporter_profile("admin-trusted")
        self.assertEqual(profile["approved"], 1)
        self.assertGreater(profile["reliability"], 0.5)
        self.assertEqual(manager.gban_intelligence.calibration()["decisions"], 1)

    def test_persistent_cross_group_behavior_can_trigger_quarantine(self):
        class TestManager(BanManager):
            STATIC_BAN_FILES = {}

        manager = TestManager(MemoryDB())
        report = manager.create_ban_report(
            "90004", "spam persistente", "admin", "group-1", evidence=["mensaje:123"]
        )
        report = manager.analyze_ban_report(
            report["id"], spam_result={"score": 75, "reasons": [{"signal": "links"}]},
            context={"local_ban_groups": ["group-1", "group-2"], "warning_count": 3,
                     "spam_events": 2, "captcha_fail_groups": ["group-1"], "ham_events": 0},
        )
        self.assertTrue(report["analysis"]["automatic_eligible"])
        self.assertIn("group-2", report["analysis"]["behavior_context"]["local_ban_groups"])

    def test_confirmed_legitimate_history_reduces_risk(self):
        class TestManager(BanManager):
            STATIC_BAN_FILES = {}

        manager = TestManager(MemoryDB())
        report = manager.create_ban_report("90005", "dudoso", "admin", "group")
        neutral = manager.gban_intelligence.assess(report, [report], spam_result={"score": 50})
        legitimate = manager.gban_intelligence.assess(
            report, [report], spam_result={"score": 50}, context={"ham_events": 3}
        )
        self.assertLess(legitimate["score"], neutral["score"])

    def test_report_renders_rich_markdown_for_editable_notification(self):
        class TestManager(BanManager):
            STATIC_BAN_FILES = {}

        manager = TestManager(MemoryDB())
        report = manager.create_ban_report("90006", "enlaces repetidos", "admin", "group")
        report = manager.analyze_ban_report(report["id"], spam_result={"score": 70, "reasons": []})
        markdown = manager.gban_intelligence.render_markdown(report)
        self.assertIn("# 🛡️", markdown)
        self.assertIn("| Riesgo |", markdown)
        self.assertIn("<details>", markdown)
        resolved = manager.gban_intelligence.render_markdown(report, "approved")
        self.assertIn("GBAN confirmado", resolved)


if __name__ == "__main__":
    unittest.main()
