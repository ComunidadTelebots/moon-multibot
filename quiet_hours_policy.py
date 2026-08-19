"""Pure, timer-free quiet-hours policy evaluation for Telegram groups."""

import datetime as dt
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_CATEGORY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")
_CENTRAL_EUROPE_ZONES = {"Europe/Madrid", "Europe/Paris", "Europe/Berlin", "Europe/Rome"}


def _last_sunday(year, month):
    day = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)


class _CentralEuropeanTime(dt.tzinfo):
    """IANA-compatible EU DST fallback for hosts without the tzdata package."""

    def utcoffset(self, value):
        return dt.timedelta(hours=1) + self.dst(value)

    def dst(self, value):
        if value is None:
            return dt.timedelta(0)
        plain = value.replace(tzinfo=None)
        start = dt.datetime.combine(_last_sunday(plain.year, 3), dt.time(2))
        end = dt.datetime.combine(_last_sunday(plain.year, 10), dt.time(3))
        return dt.timedelta(hours=1) if start <= plain < end else dt.timedelta(0)

    def tzname(self, value):
        return "CEST" if self.dst(value) else "CET"

    def fromutc(self, value):
        plain_utc = value.replace(tzinfo=None)
        start_utc = dt.datetime.combine(_last_sunday(plain_utc.year, 3), dt.time(1))
        end_utc = dt.datetime.combine(_last_sunday(plain_utc.year, 10), dt.time(1))
        offset = dt.timedelta(hours=2 if start_utc <= plain_utc < end_utc else 1)
        return (plain_utc + offset).replace(tzinfo=self)


def _zone(name):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name in _CENTRAL_EUROPE_ZONES:
            return _CentralEuropeanTime()
        raise


def _parse_time(value):
    text = str(value or "").strip()
    if not _TIME_RE.fullmatch(text):
        raise ValueError("La hora debe usar HH:MM en formato de 24 horas")
    hour, minute = (int(part) for part in text.split(":"))
    return dt.time(hour, minute)


def validate_quiet_hours_policy(policy):
    """Return a normalized copy or raise ValueError for unsafe policy data."""
    if not isinstance(policy, dict):
        raise ValueError("La política debe ser un objeto")
    enabled = policy.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("enabled debe ser booleano")
    timezone_name = str(policy.get("timezone") or "").strip()
    try:
        _zone(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Zona horaria IANA no válida") from None
    start = _parse_time(policy.get("start"))
    end = _parse_time(policy.get("end"))
    if start == end:
        raise ValueError("El inicio y el fin deben ser distintos")
    categories = policy.get("allowed_categories", [])
    if not isinstance(categories, list):
        raise ValueError("allowed_categories debe ser una lista")
    normalized_categories = []
    for category in categories:
        clean = str(category).strip().lower()
        if not _CATEGORY_RE.fullmatch(clean):
            raise ValueError("Categoría de excepción no válida")
        if clean not in normalized_categories:
            normalized_categories.append(clean)
    emergency_bypass = policy.get("emergency_bypass", True)
    if not isinstance(emergency_bypass, bool):
        raise ValueError("emergency_bypass debe ser booleano")
    return {
        "enabled": enabled,
        "timezone": timezone_name,
        "start": start.strftime("%H:%M"),
        "end": end.strftime("%H:%M"),
        "allowed_categories": normalized_categories,
        "emergency_bypass": emergency_bypass,
    }


def _aware_now(value):
    if value is None:
        return dt.datetime.now(dt.timezone.utc)
    if not isinstance(value, dt.datetime):
        raise ValueError("now debe ser datetime")
    return value.replace(tzinfo=dt.timezone.utc) if value.tzinfo is None else value


def _scheduled_quiet(policy, instant):
    if not policy["enabled"]:
        return False
    local_time = instant.astimezone(_zone(policy["timezone"])).time().replace(tzinfo=None)
    start = _parse_time(policy["start"])
    end = _parse_time(policy["end"])
    if start < end:
        return start <= local_time < end
    return local_time >= start or local_time < end


def _next_transition(policy, instant):
    if not policy["enabled"]:
        return None, None
    zone = _zone(policy["timezone"])
    local_now = instant.astimezone(zone)
    boundaries = []
    for offset in range(-1, 9):
        day = local_now.date() + dt.timedelta(days=offset)
        for name in ("start", "end"):
            boundary = dt.datetime.combine(day, _parse_time(policy[name]), tzinfo=zone)
            if boundary > local_now:
                boundaries.append(boundary)
    for boundary in sorted(set(boundaries)):
        before = _scheduled_quiet(policy, boundary - dt.timedelta(seconds=1))
        after = _scheduled_quiet(policy, boundary + dt.timedelta(seconds=1))
        if before != after:
            return boundary.isoformat(), "quiet" if after else "active"
    return None, None


def decide_quiet_hours(policy, *, category="general", emergency=False, now=None):
    """Explain whether an action should be held; never schedules or executes it."""
    normalized = validate_quiet_hours_policy(policy)
    instant = _aware_now(now)
    clean_category = str(category or "general").strip().lower()
    if not _CATEGORY_RE.fullmatch(clean_category):
        raise ValueError("Categoría no válida")
    if not isinstance(emergency, bool):
        raise ValueError("emergency debe ser booleano")
    quiet = _scheduled_quiet(normalized, instant)
    transition_at, next_state = _next_transition(normalized, instant)

    exception = None
    if quiet and emergency and normalized["emergency_bypass"]:
        exception = "emergency"
    elif quiet and clean_category in normalized["allowed_categories"]:
        exception = "allowed_category"
    held = quiet and exception is None
    if not normalized["enabled"]:
        reason = "policy_disabled"
    elif not quiet:
        reason = "outside_quiet_hours"
    elif exception:
        reason = exception
    else:
        reason = "inside_quiet_hours"
    return {
        "held": held,
        "allowed": not held,
        "scheduled_quiet": quiet,
        "reason": reason,
        "category": clean_category,
        "timezone": normalized["timezone"],
        "evaluated_at": instant.astimezone(_zone(normalized["timezone"])).isoformat(),
        "next_transition": transition_at,
        "next_state": next_state,
        "explanation": {
            "policy_enabled": normalized["enabled"],
            "window": f"{normalized['start']}-{normalized['end']}",
            "exception_applied": exception,
        },
    }
