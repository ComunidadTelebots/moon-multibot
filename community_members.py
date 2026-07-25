"""Perfiles, niveles, roles, recordatorios y preferencias comunitarias."""

import datetime
import math
import uuid


class CommunityMembers:
    ROLES = ("helper", "mentor", "expert", "moderator")

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _uid(value):
        return str(value).strip()

    def profile(self, user_id, name=None):
        uid = self._uid(user_id)
        profiles = self.db.get("COMMUNITY_PROFILES", {})
        profiles = profiles if isinstance(profiles, dict) else {}
        raw = profiles.get(uid, {}) if isinstance(profiles.get(uid), dict) else {}
        xp = max(0, int(raw.get("xp", 0)))
        level = max(1, int(math.sqrt(xp / 100)) + 1)
        return {
            "user_id": uid, "name": str(name or raw.get("name") or uid)[:100],
            "bio": str(raw.get("bio", ""))[:500], "xp": xp, "level": level,
            "next_level_xp": level * level * 100,
            "karma": int(raw.get("karma", 0)), "roles": raw.get("roles", []),
            "badges": raw.get("badges", []), "verified": bool(raw.get("verified", False)),
            "updated_at": raw.get("updated_at"),
        }

    def update_profile(self, user_id, updates):
        uid = self._uid(user_id)
        profiles = self.db.get("COMMUNITY_PROFILES", {})
        profiles = profiles if isinstance(profiles, dict) else {}
        current = self.profile(uid, updates.get("name"))
        for key in ("name", "bio"):
            if key in updates:
                current[key] = str(updates[key])[:500 if key == "bio" else 100]
        current["updated_at"] = datetime.datetime.now().isoformat()
        profiles[uid] = current
        self.db.set("COMMUNITY_PROFILES", profiles)
        return self.profile(uid)

    def verify(self, user_id, verified=True):
        uid = self._uid(user_id)
        profiles = self.db.get("COMMUNITY_PROFILES", {})
        profiles = profiles if isinstance(profiles, dict) else {}
        current = self.profile(uid)
        current["verified"] = bool(verified)
        current["updated_at"] = datetime.datetime.now().isoformat()
        profiles[uid] = current
        self.db.set("COMMUNITY_PROFILES", profiles)
        return self.profile(uid)

    def add_xp(self, user_id, amount, reason="activity"):
        uid, amount = self._uid(user_id), max(-1000, min(int(amount), 10000))
        profiles = self.db.get("COMMUNITY_PROFILES", {})
        profiles = profiles if isinstance(profiles, dict) else {}
        current = self.profile(uid)
        previous_level = current["level"]
        current["xp"] = max(0, current["xp"] + amount)
        current["updated_at"] = datetime.datetime.now().isoformat()
        profiles[uid] = current
        self.db.set("COMMUNITY_PROFILES", profiles)
        result = self.profile(uid)
        events = self.db.get("COMMUNITY_XP_EVENTS", [])
        events = events if isinstance(events, list) else []
        events.append({"user_id": uid, "amount": amount, "reason": str(reason)[:200],
                       "created_at": datetime.datetime.now().isoformat()})
        self.db.set("COMMUNITY_XP_EVENTS", events[-1000:])
        result["leveled_up"] = result["level"] > previous_level
        return result

    def request_role(self, user_id, role, reason=""):
        if role not in self.ROLES:
            return None
        rows = self.db.get("COMMUNITY_ROLE_REQUESTS", [])
        rows = rows if isinstance(rows, list) else []
        uid = self._uid(user_id)
        existing = next((row for row in rows if row.get("user_id") == uid and
                         row.get("role") == role and row.get("status") == "pending"), None)
        if existing:
            return existing
        request = {"id": uuid.uuid4().hex[:12], "user_id": self._uid(user_id),
                   "role": role, "reason": str(reason)[:500], "status": "pending",
                   "created_at": datetime.datetime.now().isoformat()}
        rows.append(request)
        self.db.set("COMMUNITY_ROLE_REQUESTS", rows[-500:])
        return request

    def resolve_role(self, request_id, decision, admin_id):
        rows = self.db.get("COMMUNITY_ROLE_REQUESTS", [])
        for row in rows if isinstance(rows, list) else []:
            if row.get("id") != request_id or row.get("status") != "pending":
                continue
            row.update({"status": decision, "resolved_by": self._uid(admin_id),
                        "resolved_at": datetime.datetime.now().isoformat()})
            if decision == "approved":
                profiles = self.db.get("COMMUNITY_PROFILES", {})
                profiles = profiles if isinstance(profiles, dict) else {}
                profile = self.profile(row["user_id"])
                profile["roles"] = list(dict.fromkeys(profile.get("roles", []) + [row["role"]]))
                profiles[row["user_id"]] = profile
                self.db.set("COMMUNITY_PROFILES", profiles)
            self.db.set("COMMUNITY_ROLE_REQUESTS", rows[-500:])
            return row
        return None

    def reminder(self, user_id, text, remind_at):
        text = str(text or "").strip()
        if not text:
            raise ValueError("escribe el recordatorio")
        when = datetime.datetime.fromisoformat(str(remind_at))
        if when <= datetime.datetime.now():
            raise ValueError("la fecha debe estar en el futuro")
        rows = self.db.get("COMMUNITY_REMINDERS", [])
        rows = rows if isinstance(rows, list) else []
        item = {"id": uuid.uuid4().hex[:12], "user_id": self._uid(user_id),
                "text": text[:500], "remind_at": when.isoformat(),
                "status": "pending", "created_at": datetime.datetime.now().isoformat()}
        rows.append(item)
        self.db.set("COMMUNITY_REMINDERS", rows[-1000:])
        return item

    def reminders(self, user_id):
        uid = self._uid(user_id)
        rows = self.db.get("COMMUNITY_REMINDERS", [])
        return [row for row in rows if row.get("user_id") == uid][-100:] if isinstance(rows, list) else []

    def due_reminders(self):
        rows = self.db.get("COMMUNITY_REMINDERS", [])
        rows = rows if isinstance(rows, list) else []
        now, due = datetime.datetime.now(), []
        for row in rows:
            if row.get("status") != "pending":
                continue
            try:
                if datetime.datetime.fromisoformat(row.get("remind_at")) <= now:
                    row["status"] = "due"
                    due.append(dict(row))
            except (TypeError, ValueError):
                row["status"] = "invalid"
        self.db.set("COMMUNITY_REMINDERS", rows[-1000:])
        return due

    def mark_reminder(self, reminder_id, status):
        rows = self.db.get("COMMUNITY_REMINDERS", [])
        for row in rows if isinstance(rows, list) else []:
            if row.get("id") == reminder_id:
                row["status"] = status
                row["delivered_at"] = datetime.datetime.now().isoformat()
                self.db.set("COMMUNITY_REMINDERS", rows[-1000:])
                return row
        return None

    def preferences(self, user_id, updates=None):
        uid = self._uid(user_id)
        values = self.db.get("COMMUNITY_NOTIFICATION_PREFS", {})
        values = values if isinstance(values, dict) else {}
        current = {"security": True, "reports": True, "events": True,
                   "reminders": True, "digest": "daily", **(values.get(uid, {}) or {})}
        if updates:
            for key in ("security", "reports", "events", "reminders"):
                if key in updates:
                    current[key] = bool(updates[key])
            if updates.get("digest") in ("off", "daily", "weekly"):
                current["digest"] = updates["digest"]
            values[uid] = current
            self.db.set("COMMUNITY_NOTIFICATION_PREFS", values)
        return current

    def role_requests(self, status=None):
        rows = self.db.get("COMMUNITY_ROLE_REQUESTS", [])
        rows = rows if isinstance(rows, list) else []
        return list(reversed([row for row in rows if not status or row.get("status") == status][-200:]))

    def directory(self):
        profiles = self.db.get("COMMUNITY_PROFILES", {})
        profiles = profiles if isinstance(profiles, dict) else {}
        return sorted(
            [self.profile(uid) for uid, row in profiles.items()
             if row.get("verified") or row.get("roles")],
            key=lambda row: (-row["level"], -row["xp"], row["name"].lower()),
        )[:500]

    def weekly_recognition(self, limit=5):
        profiles = self.db.get("COMMUNITY_PROFILES", {})
        profiles = profiles if isinstance(profiles, dict) else {}
        winners = sorted((self.profile(uid) for uid in profiles),
                         key=lambda row: (-row["xp"], -row["karma"]))[:max(1, min(int(limit), 20))]
        badge = f"colaborador-{datetime.date.today().isocalendar().year}-s{datetime.date.today().isocalendar().week}"
        for winner in winners:
            raw = profiles.get(winner["user_id"], {})
            raw["badges"] = list(dict.fromkeys((raw.get("badges") or []) + [badge]))
            profiles[winner["user_id"]] = raw
        self.db.set("COMMUNITY_PROFILES", profiles)
        history = self.db.get("COMMUNITY_RECOGNITIONS", [])
        history = history if isinstance(history, list) else []
        item = {"id": uuid.uuid4().hex[:12], "badge": badge,
                "winners": [row["user_id"] for row in winners],
                "created_at": datetime.datetime.now().isoformat()}
        history.append(item)
        self.db.set("COMMUNITY_RECOGNITIONS", history[-100:])
        return {"recognition": item, "profiles": winners}
