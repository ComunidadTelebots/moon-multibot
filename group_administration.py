"""Herramientas versionadas para administrar varios grupos de forma segura."""

import datetime
import hashlib
import json
import uuid


class GroupAdministration:
    CRITICAL_FIELDS = {"owners", "bot_permissions", "security_level", "global_ban_sync"}
    PRESETS = {
        "community": {"slow_mode": 5, "welcome": True, "links": "review", "join_approval": True},
        "support": {"slow_mode": 0, "welcome": True, "links": "allow", "join_approval": False},
        "news": {"slow_mode": 30, "welcome": False, "links": "admins", "join_approval": True},
        "gaming": {"slow_mode": 3, "welcome": True, "links": "review", "join_approval": False},
    }

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _id(value):
        return str(value).strip()

    def _configs(self):
        value = self.db.get("GROUP_ADMIN_CONFIGS", {})
        return value if isinstance(value, dict) else {}

    def _save_configs(self, value):
        self.db.set("GROUP_ADMIN_CONFIGS", value)

    def _history(self):
        value = self.db.get("GROUP_ADMIN_HISTORY", [])
        return value if isinstance(value, list) else []

    def config(self, group_id):
        gid = self._id(group_id)
        return self._configs().get(gid, {"group_id": gid, "settings": {}, "roles": {}, "version": 0})

    def setup(self, group_id, community_type, actor):
        if community_type not in self.PRESETS:
            raise ValueError("tipo de comunidad no válido")
        return self.update(group_id, {"settings": dict(self.PRESETS[community_type]), "community_type": community_type}, actor, force=True)

    def update(self, group_id, patch, actor, force=False):
        gid, configs = self._id(group_id), self._configs()
        current = configs.get(gid, {"group_id": gid, "settings": {}, "roles": {}, "version": 0})
        critical = bool(self.CRITICAL_FIELDS & set(patch))
        if critical and not force:
            return self.request_dual_approval(gid, patch, actor)
        previous = json.loads(json.dumps(current))
        for key, value in patch.items():
            if key in ("settings", "roles") and isinstance(value, dict):
                current.setdefault(key, {}).update(value)
            else:
                current[key] = value
        current["version"] = int(current.get("version", 0)) + 1
        current["updated_at"] = datetime.datetime.now().isoformat()
        current["updated_by"] = self._id(actor)
        configs[gid] = current
        self._save_configs(configs)
        history = self._history()
        history.append({"id": uuid.uuid4().hex[:12], "group_id": gid, "version": current["version"],
                        "actor": self._id(actor), "before": previous, "after": current,
                        "created_at": datetime.datetime.now().isoformat()})
        self.db.set("GROUP_ADMIN_HISTORY", history[-3000:])
        return {"status": "applied", "config": current}

    def compare(self, group_ids):
        configs = [self.config(x) for x in group_ids]
        keys = sorted({key for config in configs for key in config.get("settings", {})})
        return {"groups": [x["group_id"] for x in configs],
                "differences": {key: {x["group_id"]: x.get("settings", {}).get(key) for x in configs} for key in keys
                                if len({json.dumps(x.get("settings", {}).get(key), sort_keys=True) for x in configs}) > 1}}

    def sync(self, source_id, target_ids, fields, actor):
        source = self.config(source_id)
        allowed = [str(x) for x in fields if str(x) in source.get("settings", {})]
        results = []
        for target in target_ids:
            patch = {"settings": {key: source["settings"][key] for key in allowed}}
            results.append(self.update(target, patch, actor, force=True))
        return {"fields": allowed, "results": results}

    def restore(self, group_id, version, actor):
        snapshot = next((x for x in reversed(self._history())
                         if x.get("group_id") == self._id(group_id) and int(x.get("version", -1)) == int(version)), None)
        if not snapshot:
            return None
        restored = json.loads(json.dumps(snapshot["after"]))
        restored.pop("version", None)
        return self.update(group_id, restored, actor, force=True)

    def history(self, group_id, limit=50):
        gid = self._id(group_id)
        return [x for x in reversed(self._history()) if x.get("group_id") == gid][:max(1, min(int(limit), 200))]

    def request_dual_approval(self, group_id, patch, actor):
        rows = self.db.get("GROUP_ADMIN_APPROVALS", [])
        rows = rows if isinstance(rows, list) else []
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "patch": patch,
                "requested_by": self._id(actor), "approvals": [self._id(actor)], "status": "pending",
                "created_at": datetime.datetime.now().isoformat()}
        rows.append(item); self.db.set("GROUP_ADMIN_APPROVALS", rows[-1000:])
        return {"status": "pending_approval", "request": item}

    def approve(self, request_id, actor):
        rows = self.db.get("GROUP_ADMIN_APPROVALS", [])
        actor = self._id(actor)
        for item in rows if isinstance(rows, list) else []:
            if item.get("id") != request_id or item.get("status") != "pending":
                continue
            if actor not in item["approvals"]:
                item["approvals"].append(actor)
            if len(item["approvals"]) >= 2:
                item["status"] = "approved"
                item["resolved_at"] = datetime.datetime.now().isoformat()
                result = self.update(item["group_id"], item["patch"], actor, force=True)
            else:
                result = None
            self.db.set("GROUP_ADMIN_APPROVALS", rows[-1000:])
            return {"request": item, "result": result}
        return None

    def delegate(self, group_id, user_id, permissions, expires_at, actor):
        expiry = datetime.datetime.fromisoformat(str(expires_at))
        if expiry <= datetime.datetime.now():
            raise ValueError("la delegación debe finalizar en el futuro")
        rows = self.db.get("GROUP_ADMIN_DELEGATIONS", [])
        rows = rows if isinstance(rows, list) else []
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "user_id": self._id(user_id),
                "permissions": [str(x)[:60] for x in permissions][:30], "expires_at": expiry.isoformat(),
                "created_by": self._id(actor), "status": "active"}
        rows.append(item); self.db.set("GROUP_ADMIN_DELEGATIONS", rows[-2000:])
        return item

    def calendar_action(self, group_id, action, execute_at, payload=None):
        when = datetime.datetime.fromisoformat(str(execute_at))
        rows = self.db.get("GROUP_ADMIN_CALENDAR", [])
        rows = rows if isinstance(rows, list) else []
        item = {"id": uuid.uuid4().hex[:12], "group_id": self._id(group_id), "action": str(action)[:50],
                "execute_at": when.isoformat(), "payload": payload or {}, "status": "scheduled"}
        rows.append(item); self.db.set("GROUP_ADMIN_CALENDAR", rows[-3000:])
        return item

    def set_hours(self, group_id, timezone, schedule, actor):
        return self.update(group_id, {"opening_hours": {"timezone": str(timezone)[:80], "schedule": schedule}}, actor, force=True)

    def inactivity_candidates(self, days=60):
        cutoff = datetime.datetime.now() - datetime.timedelta(days=max(1, int(days)))
        rows = self.db.get("GROUP_ACTIVITY_INDEX", {})
        rows = rows if isinstance(rows, dict) else {}
        result = []
        for gid, stamp in rows.items():
            try:
                if datetime.datetime.fromisoformat(stamp) < cutoff:
                    result.append({"group_id": gid, "last_activity": stamp, "suggested_action": "archive"})
            except (TypeError, ValueError):
                continue
        return result

    def permission_audit(self, group_id, actual, required=None):
        required = required or ["can_delete_messages", "can_restrict_members", "can_invite_users"]
        missing = [key for key in required if not actual.get(key)]
        row = {"group_id": self._id(group_id), "missing": missing, "healthy": not missing,
               "checked_at": datetime.datetime.now().isoformat(),
               "fingerprint": hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()[:16]}
        audits = self.db.get("GROUP_PERMISSION_AUDITS", [])
        audits = audits if isinstance(audits, list) else []
        audits.append(row); self.db.set("GROUP_PERMISSION_AUDITS", audits[-2000:])
        return row

    def due_calendar_actions(self):
        now, due = datetime.datetime.now(), []
        rows = self.db.get("GROUP_ADMIN_CALENDAR", [])
        rows = rows if isinstance(rows, list) else []
        for item in rows:
            try:
                if item.get("status") == "scheduled" and datetime.datetime.fromisoformat(item["execute_at"]) <= now:
                    item["status"] = "ready"; item["ready_at"] = now.isoformat(); due.append(item)
            except (TypeError, ValueError):
                item["status"] = "invalid"
        self.db.set("GROUP_ADMIN_CALENDAR", rows[-3000:])
        return due

    def mark_calendar_action(self, action_id, status):
        rows = self.db.get("GROUP_ADMIN_CALENDAR", [])
        for item in rows if isinstance(rows, list) else []:
            if item.get("id") == action_id:
                item["status"] = status
                item["finished_at"] = datetime.datetime.now().isoformat()
                self.db.set("GROUP_ADMIN_CALENDAR", rows[-3000:])
                return item
        return None

    def defer_calendar_action(self, action_id, execute_at, reason="quiet_hours"):
        rows = self.db.get("GROUP_ADMIN_CALENDAR", [])
        for item in rows if isinstance(rows, list) else []:
            if item.get("id") == action_id:
                item.update({"status": "scheduled", "execute_at": str(execute_at),
                             "deferred_reason": str(reason), "deferred_at": datetime.datetime.now().isoformat()})
                self.db.set("GROUP_ADMIN_CALENDAR", rows[-3000:])
                return item
        return None

    def opening_transitions(self):
        """Devuelve solo cambios de estado para evitar repetir llamadas a Telegram."""
        now, transitions, configs = datetime.datetime.now(), [], self._configs()
        states = self.db.get("GROUP_OPENING_STATES", {})
        states = states if isinstance(states, dict) else {}
        weekday = str(now.weekday())
        current = now.strftime("%H:%M")
        for gid, config in configs.items():
            hours = config.get("opening_hours") or {}
            slots = (hours.get("schedule") or {}).get(weekday, [])
            should_open = any(str(slot.get("open", "00:00")) <= current < str(slot.get("close", "23:59"))
                              for slot in slots if isinstance(slot, dict))
            if slots and states.get(gid) is not should_open:
                states[gid] = should_open
                transitions.append({"group_id": gid, "open": should_open})
        self.db.set("GROUP_OPENING_STATES", states)
        return transitions

    def snapshot(self):
        now = datetime.datetime.now()
        delegations = self.db.get("GROUP_ADMIN_DELEGATIONS", [])
        for item in delegations if isinstance(delegations, list) else []:
            try:
                if item.get("status") == "active" and datetime.datetime.fromisoformat(item["expires_at"]) <= now:
                    item["status"] = "expired"
            except (TypeError, ValueError):
                item["status"] = "invalid"
        self.db.set("GROUP_ADMIN_DELEGATIONS", delegations)
        return {"configs": self._configs(), "approvals": list(reversed(self.db.get("GROUP_ADMIN_APPROVALS", []))),
                "delegations": list(reversed(delegations)), "calendar": list(reversed(self.db.get("GROUP_ADMIN_CALENDAR", []))),
                "inactive": self.inactivity_candidates(), "audits": list(reversed(self.db.get("GROUP_PERMISSION_AUDITS", [])))[:100]}
