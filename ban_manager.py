"""
Ban Manager - gestion centralizada de baneos globales y locales.
"""

import datetime
import hashlib
import secrets


class BanManager:
    """Gestiona baneos globales y baneos locales por grupo."""

    GLOBAL_KEY = "GLOBAL_BANS"
    HISTORY_KEY = "BAN_HISTORY"
    RECORDS_KEY = "COMMUNITY_BAN_RECORDS"
    REPORTS_KEY = "COMMUNITY_BAN_REPORTS"
    APPEALS_KEY = "COMMUNITY_BAN_APPEALS"
    API_KEYS_KEY = "COMMUNITY_BAN_API_KEYS"
    LEGACY_KEY = "ST_FILE"
    LOCAL_PREFIX = "BANS_"

    def __init__(self, db_manager):
        self.db = db_manager
        self.global_bans = set()
        self.load_from_db()

    def _normalize_uid(self, uid) -> str:
        return str(uid).strip()

    def _normalize_cid(self, cid) -> str:
        return str(cid).strip()

    def _empty_global(self) -> dict:
        return {"users": [], "hashes": []}

    def _empty_local(self) -> dict:
        return {"users": []}

    def _local_key(self, cid) -> str:
        return f"{self.LOCAL_PREFIX}{self._normalize_cid(cid)}"

    def _record(self, uid, reason, source, scope, cid=None, action="ban"):
        history = self.db.get(self.HISTORY_KEY, [])
        history.append({
            "uid": self._normalize_uid(uid),
            "cid": self._normalize_cid(cid) if cid is not None else None,
            "reason": reason,
            "source": source,
            "scope": scope,
            "action": action,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        self.db.set(self.HISTORY_KEY, history[-1000:])

    def _global_data(self) -> dict:
        data = self.db.get(self.GLOBAL_KEY, self._empty_global())
        if not isinstance(data, dict):
            data = self._empty_global()
        data.setdefault("users", [])
        data.setdefault("hashes", [])
        return data

    def _registry(self) -> dict:
        records = self.db.get(self.RECORDS_KEY, {})
        return records if isinstance(records, dict) else {}

    def _save_registry(self, records) -> None:
        self.db.set(self.RECORDS_KEY, records)

    @staticmethod
    def _clean_list(values, limit=20):
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            return []
        result = []
        for value in values:
            text = str(value).strip()[:500]
            if text and text not in result:
                result.append(text)
        return result[:limit]

    def _legacy_users(self) -> list:
        legacy = self.db.get(self.LEGACY_KEY, {})
        if not isinstance(legacy, dict):
            return []
        users = legacy.get("bans", [])
        return [self._normalize_uid(uid) for uid in users if self._normalize_uid(uid)]

    def _remove_legacy_user(self, uid) -> None:
        uid_str = self._normalize_uid(uid)
        legacy = self.db.get(self.LEGACY_KEY, {})
        if not isinstance(legacy, dict) or "bans" not in legacy:
            return
        users = [self._normalize_uid(item) for item in legacy.get("bans", [])]
        if uid_str in users:
            legacy["bans"] = [item for item in users if item != uid_str]
            self.db.set(self.LEGACY_KEY, legacy)

    def load_from_db(self):
        """Carga baneos globales y migra en memoria los legacy de ST_FILE."""
        data = self._global_data()
        users = {self._normalize_uid(uid) for uid in data.get("users", []) if self._normalize_uid(uid)}
        legacy_users = set(self._legacy_users())
        merged = sorted(users | legacy_users)
        self.global_bans = set(merged)
        if merged != data.get("users", []):
            data["users"] = merged
            self.db.set(self.GLOBAL_KEY, data)

    def is_global_banned(self, uid) -> bool:
        uid_str = self._normalize_uid(uid)
        if uid_str not in self.global_bans:
            return False
        record = self._registry().get(uid_str)
        if isinstance(record, dict) and self._is_expired(record):
            self._expire_ban(uid_str, record)
            return False
        return True

    @staticmethod
    def _is_expired(record):
        expires_at = record.get("expires_at") if isinstance(record, dict) else None
        if not expires_at:
            return False
        try:
            return datetime.datetime.fromisoformat(str(expires_at)) <= datetime.datetime.now()
        except (TypeError, ValueError):
            return False

    def _expire_ban(self, uid, record=None):
        uid_str = self._normalize_uid(uid)
        self.global_bans.discard(uid_str)
        data = self._global_data()
        data["users"] = [item for item in data.get("users", []) if self._normalize_uid(item) != uid_str]
        self.db.set(self.GLOBAL_KEY, data)
        records = self._registry()
        current = dict(record or records.get(uid_str) or {})
        current["user_id"] = uid_str
        current["status"] = "expired"
        current["updated_at"] = datetime.datetime.now().isoformat()
        records[uid_str] = current
        self._save_registry(records)
        self._record(uid_str, "Bloqueo temporal expirado", "automatic_expiry",
                     scope="global", action="expire")

    def get_local_bans(self, cid) -> dict:
        data = self.db.get(self._local_key(cid), self._empty_local())
        if isinstance(data, list):
            data = {"users": data}
        if not isinstance(data, dict):
            data = self._empty_local()
        data.setdefault("users", [])
        data["users"] = [self._normalize_uid(uid) for uid in data["users"] if self._normalize_uid(uid)]
        return data

    def is_local_banned(self, cid, uid) -> bool:
        return self._normalize_uid(uid) in set(self.get_local_bans(cid).get("users", []))

    def is_banned(self, uid, cid=None) -> bool:
        if self.is_global_banned(uid):
            return True
        return cid is not None and self.is_local_banned(cid, uid)

    def ban_user(self, uid, reason="", source="manual", reported_by=None,
                 evidence=None, groups=None, reviewed=True, severity="medium",
                 expires_at=None) -> bool:
        """Banea un usuario globalmente en todos los grupos."""
        uid_str = self._normalize_uid(uid)
        if not uid_str:
            return False
        created = uid_str not in self.global_bans

        self.global_bans.add(uid_str)
        data = self._global_data()
        if uid_str not in data["users"]:
            data["users"].append(uid_str)
        self.db.set(self.GLOBAL_KEY, data)
        now = datetime.datetime.now().isoformat()
        records = self._registry()
        previous = records.get(uid_str, {}) if isinstance(records.get(uid_str), dict) else {}
        records[uid_str] = {
            "user_id": uid_str,
            "status": "active",
            "reason": str(reason or previous.get("reason") or "").strip()[:1000],
            "source": str(source or previous.get("source") or "manual").strip()[:100],
            "evidence": self._clean_list(evidence or previous.get("evidence", [])),
            "groups": self._clean_list(groups or previous.get("groups", []), limit=50),
            "reported_by": str(reported_by) if reported_by is not None else previous.get("reported_by"),
            "reviewed": bool(reviewed),
            "reviewed_by": str(reported_by) if reviewed and reported_by is not None else previous.get("reviewed_by"),
            "severity": severity if severity in ("low", "medium", "high", "critical") else "medium",
            "expires_at": str(expires_at) if expires_at else None,
            "created_at": previous.get("created_at") or now,
            "updated_at": now,
        }
        self._save_registry(records)
        if created:
            self._record(uid_str, reason, source, scope="global")
        return created

    def ban_local_user(self, cid, uid, reason="", source="manual") -> bool:
        """Banea un usuario solo para un grupo concreto."""
        uid_str = self._normalize_uid(uid)
        cid_str = self._normalize_cid(cid)
        if not uid_str or not cid_str:
            return False

        data = self.get_local_bans(cid_str)
        if uid_str in data["users"]:
            return False

        data["users"].append(uid_str)
        self.db.set(self._local_key(cid_str), data)
        self._record(uid_str, reason, source, scope="local", cid=cid_str)
        return True

    def unban_user(self, uid) -> bool:
        uid_str = self._normalize_uid(uid)
        if uid_str not in self.global_bans:
            return False

        self.global_bans.discard(uid_str)
        data = self._global_data()
        if uid_str in data["users"]:
            data["users"].remove(uid_str)
        self.db.set(self.GLOBAL_KEY, data)
        self._remove_legacy_user(uid_str)
        records = self._registry()
        record = records.get(uid_str) if isinstance(records.get(uid_str), dict) else {
            "user_id": uid_str, "reason": "", "source": "legacy",
            "evidence": [], "groups": [], "reviewed": True,
            "created_at": None,
        }
        record["status"] = "revoked"
        record["updated_at"] = datetime.datetime.now().isoformat()
        records[uid_str] = record
        self._save_registry(records)
        self._record(uid_str, "Manual global unban", "manual", scope="global", action="unban")
        return True

    def unban_local_user(self, cid, uid) -> bool:
        uid_str = self._normalize_uid(uid)
        cid_str = self._normalize_cid(cid)
        data = self.get_local_bans(cid_str)
        if uid_str not in data["users"]:
            return False

        data["users"].remove(uid_str)
        self.db.set(self._local_key(cid_str), data)
        self._record(uid_str, "Manual local unban", "manual", scope="local", cid=cid_str, action="unban")
        return True

    def get_all_bans(self) -> dict:
        return self._global_data()

    def get_ban_record(self, uid):
        uid_str = self._normalize_uid(uid)
        record = self._registry().get(uid_str)
        if isinstance(record, dict):
            if record.get("status", "active") == "active" and self._is_expired(record):
                self._expire_ban(uid_str, record)
                record = self._registry().get(uid_str)
            return dict(record)
        if self.is_global_banned(uid_str):
            return {
                "user_id": uid_str, "status": "active", "reason": "",
                "source": "legacy", "evidence": [], "groups": [],
                "reviewed": True, "severity": "medium", "expires_at": None,
                "created_at": None, "updated_at": None,
            }
        return None

    def list_ban_records(self, query="", status="active", limit=500):
        query = str(query or "").strip().lower()
        records = self._registry()
        # Los baneos anteriores a este registro siguen siendo visibles y editables.
        for uid in self.global_bans:
            records.setdefault(uid, self.get_ban_record(uid))
        for uid, record in list(records.items()):
            if isinstance(record, dict) and record.get("status", "active") == "active" and self._is_expired(record):
                self._expire_ban(uid, record)
        records = self._registry()
        for uid in self.global_bans:
            records.setdefault(uid, self.get_ban_record(uid))
        rows = []
        for record in records.values():
            if not isinstance(record, dict):
                continue
            current = record.get("status", "active")
            haystack = f"{record.get('user_id', '')} {record.get('reason', '')} {record.get('source', '')}".lower()
            if status != "all" and current != status:
                continue
            if query and query not in haystack:
                continue
            rows.append(dict(record))
        rows.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def review_ban_record(self, uid, reviewed_by=None, reason=None, evidence=None):
        uid_str = self._normalize_uid(uid)
        records = self._registry()
        record = records.get(uid_str)
        if not isinstance(record, dict):
            return None
        if reason is not None:
            record["reason"] = str(reason).strip()[:1000]
        if evidence is not None:
            record["evidence"] = self._clean_list(evidence)
        record["reviewed"] = True
        record["reviewed_by"] = str(reviewed_by) if reviewed_by is not None else None
        record["updated_at"] = datetime.datetime.now().isoformat()
        records[uid_str] = record
        self._save_registry(records)
        return dict(record)

    def create_ban_report(self, uid, reason, reported_by, chat_id, evidence=None):
        uid_str = self._normalize_uid(uid)
        reason = str(reason or "").strip()[:1000]
        if not uid_str or not reason:
            return None
        reports = self.db.get(self.REPORTS_KEY, [])
        if not isinstance(reports, list):
            reports = []
        now = datetime.datetime.now().isoformat()
        report = {
            "id": f"{int(datetime.datetime.now().timestamp() * 1000)}-{uid_str}",
            "user_id": uid_str,
            "reason": reason,
            "evidence": self._clean_list(evidence),
            "reported_by": str(reported_by),
            "chat_id": self._normalize_cid(chat_id),
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "resolved_by": None,
        }
        reports.append(report)
        self.db.set(self.REPORTS_KEY, reports[-2000:])
        return dict(report)

    def list_ban_reports(self, status="pending", limit=500):
        reports = self.db.get(self.REPORTS_KEY, [])
        if not isinstance(reports, list):
            return []
        rows = [
            dict(item) for item in reports if isinstance(item, dict)
            and (status == "all" or item.get("status", "pending") == status)
        ]
        rows.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def resolve_ban_report(self, report_id, decision, resolved_by):
        if decision not in ("approved", "rejected"):
            return None
        reports = self.db.get(self.REPORTS_KEY, [])
        if not isinstance(reports, list):
            return None
        result = None
        for report in reports:
            if not isinstance(report, dict) or str(report.get("id")) != str(report_id):
                continue
            if report.get("status", "pending") != "pending":
                return None
            report["status"] = decision
            report["resolved_by"] = str(resolved_by)
            report["updated_at"] = datetime.datetime.now().isoformat()
            result = dict(report)
            break
        if result:
            self.db.set(self.REPORTS_KEY, reports[-2000:])
        return result

    def create_ban_appeal(self, uid, message):
        uid_str = self._normalize_uid(uid)
        message = str(message or "").strip()[:2000]
        record = self.get_ban_record(uid_str)
        if not uid_str or not message or not record or record.get("status") != "active":
            return None
        appeals = self.db.get(self.APPEALS_KEY, [])
        if not isinstance(appeals, list):
            appeals = []
        if any(
            isinstance(item, dict) and item.get("status", "pending") == "pending"
            and self._normalize_uid(item.get("user_id")) == uid_str
            for item in appeals
        ):
            return False
        now = datetime.datetime.now().isoformat()
        appeal = {
            "id": f"{int(datetime.datetime.now().timestamp() * 1000)}-{uid_str}",
            "user_id": uid_str,
            "message": message,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "resolved_by": None,
        }
        appeals.append(appeal)
        self.db.set(self.APPEALS_KEY, appeals[-2000:])
        return dict(appeal)

    def list_ban_appeals(self, status="pending", limit=500, uid=None):
        appeals = self.db.get(self.APPEALS_KEY, [])
        if not isinstance(appeals, list):
            return []
        uid_str = self._normalize_uid(uid) if uid is not None else None
        rows = [
            dict(item) for item in appeals if isinstance(item, dict)
            and (status == "all" or item.get("status", "pending") == status)
            and (uid_str is None or self._normalize_uid(item.get("user_id")) == uid_str)
        ]
        rows.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
        return rows[:max(1, min(int(limit), 2000))]

    def resolve_ban_appeal(self, appeal_id, decision, resolved_by):
        if decision not in ("approved", "rejected"):
            return None
        appeals = self.db.get(self.APPEALS_KEY, [])
        if not isinstance(appeals, list):
            return None
        result = None
        for appeal in appeals:
            if not isinstance(appeal, dict) or str(appeal.get("id")) != str(appeal_id):
                continue
            if appeal.get("status", "pending") != "pending":
                return None
            appeal["status"] = decision
            appeal["resolved_by"] = str(resolved_by)
            appeal["updated_at"] = datetime.datetime.now().isoformat()
            result = dict(appeal)
            break
        if result:
            self.db.set(self.APPEALS_KEY, appeals[-2000:])
        return result

    def create_api_key(self, label, created_by):
        label = str(label or "").strip()[:80]
        if not label:
            return None
        raw_key = f"ctb_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        keys = self.db.get(self.API_KEYS_KEY, {})
        if not isinstance(keys, dict):
            keys = {}
        now = datetime.datetime.now().isoformat()
        keys[key_hash] = {
            "id": key_hash[:12],
            "label": label,
            "active": True,
            "scope": "registry:check",
            "created_by": str(created_by),
            "created_at": now,
            "last_used_at": None,
        }
        self.db.set(self.API_KEYS_KEY, keys)
        return {"key": raw_key, **dict(keys[key_hash])}

    def list_api_keys(self):
        keys = self.db.get(self.API_KEYS_KEY, {})
        if not isinstance(keys, dict):
            return []
        rows = [dict(item) for item in keys.values() if isinstance(item, dict)]
        rows.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return rows

    def revoke_api_key(self, key_id):
        keys = self.db.get(self.API_KEYS_KEY, {})
        if not isinstance(keys, dict):
            return False
        for key_hash, item in keys.items():
            if isinstance(item, dict) and item.get("id") == str(key_id) and item.get("active"):
                item["active"] = False
                item["revoked_at"] = datetime.datetime.now().isoformat()
                keys[key_hash] = item
                self.db.set(self.API_KEYS_KEY, keys)
                return True
        return False

    def authenticate_api_key(self, raw_key):
        raw_key = str(raw_key or "")
        if not raw_key.startswith("ctb_"):
            return None
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        keys = self.db.get(self.API_KEYS_KEY, {})
        item = keys.get(key_hash) if isinstance(keys, dict) else None
        if not isinstance(item, dict) or not item.get("active"):
            return None
        now = datetime.datetime.now()
        try:
            last_used = datetime.datetime.fromisoformat(item.get("last_used_at") or "")
        except (TypeError, ValueError):
            last_used = None
        # Evita una escritura en la base por cada consulta de bots externos.
        if last_used is None or last_used < now - datetime.timedelta(minutes=5):
            item["last_used_at"] = now.isoformat()
            keys[key_hash] = item
            self.db.set(self.API_KEYS_KEY, keys)
        return dict(item)

    def get_all_local_bans(self) -> dict:
        keys = self.db.keys(self.LOCAL_PREFIX) if hasattr(self.db, "keys") else []
        result = {}
        for key in keys:
            cid = key[len(self.LOCAL_PREFIX):]
            result[cid] = self.get_local_bans(cid).get("users", [])
        return result

    def get_ban_history(self, limit=100) -> list:
        history = self.db.get(self.HISTORY_KEY, [])
        return history[-limit:]

    def get_ban_stats(self) -> dict:
        global_data = self.get_all_bans()
        local_data = self.get_all_local_bans()
        history = self.get_ban_history(1000)

        sources = {}
        for record in history:
            source = record.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        now = datetime.datetime.now()
        recent = 0
        for record in history:
            try:
                if datetime.datetime.fromisoformat(record["timestamp"]) > now - datetime.timedelta(days=1):
                    recent += 1
            except Exception:
                pass

        return {
            "total_banned_users": len(global_data.get("users", [])),
            "total_local_banned_users": sum(len(users) for users in local_data.values()),
            "groups_with_local_bans": len([users for users in local_data.values() if users]),
            "total_banned_hashes": len(global_data.get("hashes", [])),
            "recent_bans": recent,
            "sources": sources,
        }

    def sync_with_cas(self, uid, cas_banned) -> bool:
        if cas_banned and not self.is_global_banned(uid):
            return self.ban_user(uid, reason="CAS global blacklist", source="cas")
        return False
