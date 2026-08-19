"""Pure, persistable reminder scheduling primitives with no background effects."""

from __future__ import annotations

import copy
import datetime as dt
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = dt.timezone.utc
RECURRENCES = {"once", "daily", "weekly"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _last_sunday(year, month):
    last = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() + 1) % 7)


class _EuropeMadrid(dt.tzinfo):
    """Stdlib-only fallback for the EU timezone when host tzdata is unavailable."""

    def utcoffset(self, value):
        if value is None:
            return None
        naive = value.replace(tzinfo=None)
        start = dt.datetime(value.year, 3, _last_sunday(value.year, 3).day, 2)
        end = dt.datetime(value.year, 10, _last_sunday(value.year, 10).day, 3)
        if start <= naive < end:
            if naive.date() == end.date() and naive.hour == 2 and value.fold == 1:
                return dt.timedelta(hours=1)
            return dt.timedelta(hours=2)
        if naive.date() == start.date() and naive.hour == 2 and value.fold == 0:
            return dt.timedelta(hours=1)
        return dt.timedelta(hours=1)

    def dst(self, value):
        offset = self.utcoffset(value)
        return None if offset is None else offset - dt.timedelta(hours=1)

    def tzname(self, value):
        return "CEST" if self.dst(value) else "CET"

    def fromutc(self, value):
        utc = value.replace(tzinfo=None)
        start = dt.datetime(value.year, 3, _last_sunday(value.year, 3).day, 1)
        end = dt.datetime(value.year, 10, _last_sunday(value.year, 10).day, 1)
        offset = dt.timedelta(hours=2) if start <= utc < end else dt.timedelta(hours=1)
        local = (utc + offset).replace(tzinfo=self)
        if end <= utc < end + dt.timedelta(hours=1):
            local = local.replace(fold=1)
        return local


def _utc(value, field="date"):
    if isinstance(value, str):
        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, dt.datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must include a UTC offset")
    return value.astimezone(UTC)


def _iso(value):
    return _utc(value).isoformat().replace("+00:00", "Z")


def _zone(name):
    if not isinstance(name, str) or "/" not in name:
        raise ValueError("timezone must be an IANA zone")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as error:
        if name in ("Etc/UTC", "UTC"):
            return UTC
        if name == "Europe/Madrid":
            return _EuropeMadrid()
        raise ValueError("timezone must be an IANA zone") from error


def _local(value):
    if not isinstance(value, str):
        raise ValueError("local_time must be an ISO local datetime")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("local_time must be an ISO local datetime") from error
    if parsed.tzinfo is not None or parsed.second or parsed.microsecond:
        raise ValueError("local_time must be timezone-naive and minute-precise")
    return parsed


def _local_candidates(local, zone):
    candidates = []
    for fold in (0, 1):
        candidate = local.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        round_trip = candidate.astimezone(zone).replace(tzinfo=None)
        if round_trip == local and candidate not in candidates:
            candidates.append(candidate)
    return sorted(candidates)


def _resolve_local(local, zone, fold=None):
    candidates = _local_candidates(local, zone)
    if not candidates:
        raise ValueError("local_time does not exist because of a DST transition")
    if len(candidates) == 2:
        if fold not in (0, 1):
            raise ValueError("ambiguous DST local_time requires fold 0 or 1")
        return candidates[fold]
    if fold not in (None, 0):
        raise ValueError("fold 1 is only valid for an ambiguous DST local_time")
    return candidates[0]


def _validated(reminder):
    if not isinstance(reminder, dict):
        raise ValueError("reminder must be an object")
    required = {"id", "text", "timezone", "local_time", "recurrence", "next_run", "status"}
    if not required.issubset(reminder):
        raise ValueError("reminder is incomplete")
    if not ID_PATTERN.fullmatch(str(reminder["id"])):
        raise ValueError("reminder id must be opaque")
    if not isinstance(reminder["text"], str) or not reminder["text"].strip() or len(reminder["text"]) > 500:
        raise ValueError("reminder text must contain 1 to 500 characters")
    _zone(reminder["timezone"])
    _local(reminder["local_time"])
    if reminder["recurrence"] not in RECURRENCES:
        raise ValueError("unsupported recurrence")
    _utc(reminder["next_run"], "next_run")
    if reminder["status"] not in {"pending", "due", "cancelled"}:
        raise ValueError("unsupported reminder status")
    return reminder


def create_reminder(reminder_id, text, local_time, timezone, recurrence="once", fold=None, now=None):
    if not ID_PATTERN.fullmatch(str(reminder_id or "")):
        raise ValueError("reminder id must be opaque")
    text = str(text or "").strip()
    if not text or len(text) > 500:
        raise ValueError("reminder text must contain 1 to 500 characters")
    if recurrence not in RECURRENCES:
        raise ValueError("unsupported recurrence")
    local = _local(local_time)
    run = _resolve_local(local, _zone(timezone), fold)
    reference = _utc(now or dt.datetime.now(UTC), "now")
    if run <= reference:
        raise ValueError("next_run must be in the future")
    return {
        "id": str(reminder_id), "text": text, "timezone": timezone,
        "local_time": local.isoformat(timespec="minutes"), "recurrence": recurrence,
        "fold": fold, "next_run": _iso(run), "status": "pending",
    }


def add_reminder(reminders, reminder):
    items = copy.deepcopy(list(reminders))
    item = copy.deepcopy(_validated(reminder))
    if any(existing.get("id") == item["id"] for existing in items):
        raise ValueError("reminder ids must be unique")
    items.append(item)
    return items


def _next_occurrence(reminder, after):
    zone = _zone(reminder["timezone"])
    local = _local(reminder["local_time"])
    step = dt.timedelta(days=1 if reminder["recurrence"] == "daily" else 7)
    candidate = local + step
    for _ in range(370):
        matches = _local_candidates(candidate, zone)
        valid = [value for value in matches if value > after]
        if valid:
            index = reminder.get("fold") if len(valid) == 2 and reminder.get("fold") in (0, 1) else 0
            chosen = valid[min(index, len(valid) - 1)]
            return candidate, chosen
        candidate += step
    raise ValueError("unable to calculate recurring next_run")


def calculate_due(reminders, now):
    """Return (due occurrences, new state); consuming the new state is idempotent."""
    instant = _utc(now, "now")
    items = copy.deepcopy(list(reminders))
    ids = [item.get("id") for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("reminder ids must be unique")
    due = []
    for item in items:
        _validated(item)
        if item["status"] != "pending" or _utc(item["next_run"]) > instant:
            continue
        occurrence = item["next_run"]
        if item.get("last_due_at") == occurrence:
            continue
        due.append({"id": item["id"], "text": item["text"], "due_at": occurrence})
        item["last_due_at"] = occurrence
        if item["recurrence"] == "once":
            item["status"] = "due"
        else:
            local, run = _next_occurrence(item, instant)
            item["local_time"] = local.isoformat(timespec="minutes")
            item["next_run"] = _iso(run)
    return due, items


def snooze_reminder(reminder, minutes, now):
    item = copy.deepcopy(_validated(reminder))
    if item["status"] == "cancelled":
        raise ValueError("cancelled reminders cannot be snoozed")
    if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 10080:
        raise ValueError("snooze must be between 1 minute and 7 days")
    run = _utc(now, "now") + dt.timedelta(minutes=minutes)
    item.update({"next_run": _iso(run), "status": "pending", "snoozed_until": _iso(run)})
    item.pop("last_due_at", None)
    return item


def cancel_reminder(reminder, now):
    item = copy.deepcopy(_validated(reminder))
    if item["status"] != "cancelled":
        item.update({"status": "cancelled", "cancelled_at": _iso(now)})
    return item


def serialize_reminders(reminders):
    items = copy.deepcopy(list(reminders))
    ids = []
    for item in items:
        _validated(item)
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("reminder ids must be unique")
    return json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_reminders(payload):
    try:
        items = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("invalid reminder serialization") from error
    if not isinstance(items, list):
        raise ValueError("serialized reminders must be a list")
    serialize_reminders(items)
    return items
