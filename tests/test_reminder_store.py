import datetime as dt
import unittest

from plugins.reminder_store import (
    add_reminder,
    calculate_due,
    cancel_reminder,
    create_reminder,
    deserialize_reminders,
    serialize_reminders,
    snooze_reminder,
)


class ReminderStoreTests(unittest.TestCase):
    def make(self, **overrides):
        values = {
            "reminder_id": "rem-1", "text": "Revisar moderación",
            "local_time": "2026-07-30T12:00", "timezone": "Europe/Madrid",
            "now": "2026-07-30T09:00:00Z",
        }
        values.update(overrides)
        return create_reminder(**values)

    def test_validates_and_enforces_unique_persisted_ids(self):
        reminder = self.make()
        self.assertEqual(reminder["next_run"], "2026-07-30T10:00:00Z")
        self.assertRaises(ValueError, self.make, timezone="Madrid")
        self.assertRaises(ValueError, self.make, recurrence="hourly")
        self.assertRaises(ValueError, add_reminder, [reminder], reminder)

    def test_dst_gap_is_rejected_and_fold_requires_explicit_choice(self):
        gap = {"local_time": "2026-03-29T02:30", "now": "2026-03-28T00:00:00Z"}
        self.assertRaisesRegex(ValueError, "does not exist", self.make, **gap)
        fold = {"local_time": "2026-10-25T02:30", "now": "2026-10-24T00:00:00Z"}
        self.assertRaisesRegex(ValueError, "ambiguous", self.make, **fold)
        first = self.make(**fold, fold=0)
        second = self.make(**fold, fold=1)
        self.assertEqual(first["next_run"], "2026-10-25T00:30:00Z")
        self.assertEqual(second["next_run"], "2026-10-25T01:30:00Z")
        recurring = self.make(
            local_time="2026-03-28T02:30", recurrence="daily", now="2026-03-27T00:00:00Z"
        )
        _, state = calculate_due([recurring], "2026-03-28T02:00:00Z")
        self.assertEqual(state[0]["next_run"], "2026-03-30T00:30:00Z")

    def test_due_calculation_is_idempotent_for_once_and_recurring(self):
        once = self.make()
        daily = self.make(reminder_id="rem-2", recurrence="daily")
        source = [once, daily]
        original = [dict(item) for item in source]
        due, state = calculate_due(source, "2026-07-30T10:01:00Z")
        self.assertEqual([item["id"] for item in due], ["rem-1", "rem-2"])
        self.assertEqual(source, original)
        self.assertEqual(state[0]["status"], "due")
        self.assertEqual(state[1]["next_run"], "2026-07-31T10:00:00Z")
        repeated, repeated_state = calculate_due(state, "2026-07-30T10:01:00Z")
        self.assertEqual(repeated, [])
        self.assertEqual(repeated_state, state)

    def test_snooze_and_cancel_are_pure_and_cancelled_is_never_due(self):
        reminder = self.make()
        snoozed = snooze_reminder(reminder, 15, "2026-07-30T10:00:00Z")
        self.assertEqual(snoozed["next_run"], "2026-07-30T10:15:00Z")
        self.assertNotIn("snoozed_until", reminder)
        cancelled = cancel_reminder(snoozed, "2026-07-30T10:05:00Z")
        due, _ = calculate_due([cancelled], "2026-07-31T10:00:00Z")
        self.assertEqual(due, [])
        self.assertEqual(cancelled["status"], "cancelled")

    def test_serialization_round_trip_is_deterministic(self):
        reminders = [self.make(), self.make(reminder_id="rem-2", recurrence="weekly")]
        payload = serialize_reminders(reminders)
        restored = deserialize_reminders(payload)
        self.assertEqual(restored, reminders)
        self.assertEqual(serialize_reminders(restored), payload)
        self.assertNotIn(str(dt.datetime.now()), payload)
        self.assertRaises(ValueError, deserialize_reminders, "not-json")


if __name__ == "__main__":
    unittest.main()
