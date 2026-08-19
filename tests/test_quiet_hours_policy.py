import datetime as dt
import unittest

from quiet_hours_policy import decide_quiet_hours, validate_quiet_hours_policy


class QuietHoursPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "enabled": True,
            "timezone": "Europe/Madrid",
            "start": "23:00",
            "end": "07:00",
            "allowed_categories": ["security"],
            "emergency_bypass": True,
        }

    def test_cross_midnight_window_and_next_transition(self):
        decision = decide_quiet_hours(
            self.policy, now=dt.datetime(2026, 1, 15, 23, 30, tzinfo=dt.timezone.utc)
        )
        self.assertTrue(decision["held"])
        self.assertEqual(decision["reason"], "inside_quiet_hours")
        self.assertEqual(decision["evaluated_at"], "2026-01-16T00:30:00+01:00")
        self.assertEqual(decision["next_transition"], "2026-01-16T07:00:00+01:00")
        self.assertEqual(decision["next_state"], "active")

    def test_daytime_window_enters_at_next_start(self):
        policy = {**self.policy, "start": "09:00", "end": "17:00"}
        decision = decide_quiet_hours(
            policy, now=dt.datetime(2026, 1, 15, 7, 0, tzinfo=dt.timezone.utc)
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "outside_quiet_hours")
        self.assertEqual(decision["next_transition"], "2026-01-15T09:00:00+01:00")
        self.assertEqual(decision["next_state"], "quiet")

    def test_iana_zone_applies_summer_offset(self):
        decision = decide_quiet_hours(
            self.policy, now=dt.datetime(2026, 7, 15, 21, 30, tzinfo=dt.timezone.utc)
        )
        self.assertTrue(decision["held"])
        self.assertEqual(decision["evaluated_at"], "2026-07-15T23:30:00+02:00")
        self.assertEqual(decision["next_transition"], "2026-07-16T07:00:00+02:00")

    def test_emergency_and_allowlisted_category_are_explainable_bypasses(self):
        instant = dt.datetime(2026, 1, 15, 23, 30, tzinfo=dt.timezone.utc)
        emergency = decide_quiet_hours(self.policy, emergency=True, now=instant)
        security = decide_quiet_hours(self.policy, category="security", now=instant)
        regular = decide_quiet_hours(self.policy, category="news", now=instant)
        self.assertEqual(emergency["reason"], "emergency")
        self.assertEqual(security["reason"], "allowed_category")
        self.assertTrue(emergency["allowed"] and security["allowed"])
        self.assertTrue(regular["held"])

    def test_disabled_policy_has_no_transition(self):
        decision = decide_quiet_hours(
            {**self.policy, "enabled": False}, now=dt.datetime(2026, 1, 15, tzinfo=dt.timezone.utc)
        )
        self.assertEqual(decision["reason"], "policy_disabled")
        self.assertIsNone(decision["next_transition"])
        self.assertTrue(decision["allowed"])

    def test_validates_iana_zone_times_categories_and_input_immutability(self):
        before = dict(self.policy)
        normalized = validate_quiet_hours_policy(self.policy)
        self.assertEqual(normalized["timezone"], "Europe/Madrid")
        self.assertEqual(self.policy, before)
        with self.assertRaisesRegex(ValueError, "IANA"):
            validate_quiet_hours_policy({**self.policy, "timezone": "Madrid"})
        with self.assertRaisesRegex(ValueError, "HH:MM"):
            validate_quiet_hours_policy({**self.policy, "start": "25:00"})
        with self.assertRaisesRegex(ValueError, "Categoría"):
            validate_quiet_hours_policy({**self.policy, "allowed_categories": ["bad value"]})


if __name__ == "__main__":
    unittest.main()
