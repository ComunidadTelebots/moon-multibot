"""Funciones avanzadas de gestión de grupos, compartidas por web y Mini App."""

import datetime
import re
import time
import uuid
from collections import Counter


class GroupSuite:
    PURPOSES = ("member", "verified", "collaborator", "moderator", "watch", "guest")

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _cid(chat_id):
        return str(chat_id)

    @staticmethod
    def _uid(user_id):
        return str(user_id)

    def config(self, chat_id):
        cid = self._cid(chat_id)
        raw = self.db.get(f"GROUPSUITE_{cid}", {})
        if not isinstance(raw, dict):
            raw = {}
        def section(name):
            value = raw.get(name, {})
            return value if isinstance(value, dict) else {}
        quarantine, raid = section("quarantine"), section("raid")
        welcome, consensus = section("welcome"), section("consensus")
        media = section("media_security")
        appearance = section("appearance")
        slow = section("adaptive_slow")
        limits = section("content_limits")
        channel_senders = section("channel_senders")
        bot_interaction = section("bot_interaction")
        flood = section("flood_control")
        media_controls = section("media_controls")
        accent = str(appearance.get("accent", "teal"))
        if accent not in ("teal", "blue", "violet", "amber", "rose"):
            accent = "teal"
        action = str(media.get("action", "notify"))
        if action not in ("notify", "delete", "ban"):
            action = "notify"
        return {
            "quarantine": {
                "enabled": bool(quarantine.get("enabled", False)),
                "hours": max(1, min(int(quarantine.get("hours", 24)), 168)),
                "messages": max(1, min(int(quarantine.get("messages", 5)), 50)),
                "block_links": bool(quarantine.get("block_links", True)),
            },
            "raid": {
                "enabled": bool(raid.get("enabled", True)),
                "joins": max(3, min(int(raid.get("joins", 8)), 100)),
                "window_seconds": max(10, min(int(raid.get("window_seconds", 60)), 600)),
                "lock_minutes": max(1, min(int(raid.get("lock_minutes", 15)), 180)),
            },
            "welcome": {
                "enabled": bool(welcome.get("enabled", False)),
                "message": str(welcome.get(
                    "message", "Bienvenido, {name}. Revisa las reglas del grupo."
                ))[:1000],
                "delete_after": max(0, min(int(welcome.get("delete_after", 0)), 86400)),
            },
            "consensus": {
                "enabled": bool(consensus.get("enabled", True)),
                "votes_required": max(1, min(int(consensus.get("votes_required", 2)), 10)),
            },
            "media_security": {
                "enabled": bool(media.get("enabled", False)),
                "scan_photos": bool(media.get("scan_photos", True)),
                "scan_links": bool(media.get("scan_links", False)),
                "scan_files": bool(media.get("scan_files", False)),
                "ocr": bool(media.get("ocr", True)),
                "impersonation": bool(media.get("impersonation", True)),
                "sensitive": bool(media.get("sensitive", False)),
                "threshold": max(20, min(int(media.get("threshold", 60)), 100)),
                "vt_malicious": max(1, min(int(media.get("vt_malicious", 3)), 25)),
                "action": action,
                "notify_admins": bool(media.get("notify_admins", True)),
                "notify_master": bool(media.get("notify_master", True)),
            },
            "appearance": {
                "accent": accent,
                "compact": bool(appearance.get("compact", False)),
            },
            "adaptive_slow": {
                "enabled": bool(slow.get("enabled", False)),
                "base_seconds": max(0, min(int(slow.get("base_seconds", 2)), 30)),
                "busy_messages": max(10, min(int(slow.get("busy_messages", 40)), 300)),
                "max_seconds": max(2, min(int(slow.get("max_seconds", 15)), 120)),
            },
            "content_limits": {
                "enabled": bool(limits.get("enabled", False)),
                "mentions": max(1, min(int(limits.get("mentions", 6)), 50)),
                "emojis": max(3, min(int(limits.get("emojis", 20)), 200)),
                "uppercase_percent": max(20, min(int(limits.get("uppercase_percent", 75)), 100)),
                "action": str(limits.get("action", "delete")) if str(limits.get("action", "delete")) in ("observe", "delete", "warn") else "delete",
            },
            "channel_senders": {
                "ban_external_channels": bool(channel_senders.get("ban_external_channels", False)),
                "delete_messages": bool(channel_senders.get("delete_messages", True)),
                "notify": bool(channel_senders.get("notify", True)),
            },
            "bot_interaction": {
                "enabled": bool(bot_interaction.get("enabled", False)),
                "learn": bool(bot_interaction.get("learn", True)),
                "reply": bool(bot_interaction.get("reply", False)),
                "allowed_usernames": [
                    str(item).lower().lstrip("@")[:64]
                    for item in bot_interaction.get("allowed_usernames", [])
                    if str(item).strip()
                ][:50],
                "max_replies_per_hour": max(1, min(int(bot_interaction.get("max_replies_per_hour", 5)), 30)),
            },
            "flood_control": {
                "enabled": bool(flood.get("enabled", False)),
                "messages": max(3, min(int(flood.get("messages", 8)), 50)),
                "window_seconds": max(2, min(int(flood.get("window_seconds", 10)), 300)),
                "mute_minutes": max(1, min(int(flood.get("mute_minutes", 10)), 1440)),
                "strikes_before_ban": max(0, min(int(flood.get("strikes_before_ban", 3)), 20)),
                "delete_messages": bool(flood.get("delete_messages", True)),
            },
            "media_controls": {
                "enabled": bool(media_controls.get("enabled", False)),
                "blocked_types": [
                    str(value) for value in media_controls.get("blocked_types", [])
                    if str(value) in ("photo", "video", "audio", "voice", "document", "sticker", "animation", "video_note")
                ],
                "max_file_mb": max(1, min(int(media_controls.get("max_file_mb", 20)), 200)),
                "action": str(media_controls.get("action", "delete")) if str(media_controls.get("action", "delete")) in ("delete", "mute", "ban") else "delete",
                "mute_minutes": max(1, min(int(media_controls.get("mute_minutes", 10)), 1440)),
                "notify": bool(media_controls.get("notify", True)),
            },
            "rules": raw.get("rules", []) if isinstance(raw.get("rules"), list) else [],
        }

    def save_config(self, chat_id, updates):
        current = self.config(chat_id)
        for section in ("quarantine", "raid", "welcome", "consensus", "media_security", "appearance", "adaptive_slow", "content_limits", "channel_senders", "bot_interaction", "flood_control", "media_controls"):
            if isinstance(updates.get(section), dict):
                current[section].update(updates[section])
        if isinstance(updates.get("rules"), list):
            current["rules"] = updates["rules"][:30]
        self.db.set(f"GROUPSUITE_{self._cid(chat_id)}", current)
        return self.config(chat_id)

    def media_decision(self, chat_id, result, source="vision"):
        """Evalúa un resultado; nunca ejecuta acciones de Telegram por sí mismo."""
        cid = self._cid(chat_id)
        cfg = self.config(cid)["media_security"]
        score = int(result.get("score", 0) or 0)
        malicious = int(result.get("malicious", 0) or 0)
        suspicious = int(result.get("suspicious", 0) or 0)
        matched = score >= cfg["threshold"] or malicious >= cfg["vt_malicious"]
        decision = {
            "matched": matched,
            "action": cfg["action"] if matched else "allow",
            "source": source,
            "score": score,
            "malicious": malicious,
            "suspicious": suspicious,
            "threshold": cfg["threshold"],
            "reason": (
                f"riesgo visual {score}/{cfg['threshold']}" if source == "vision"
                else f"{malicious} detecciones maliciosas"
            ),
            "created_at": datetime.datetime.now().isoformat(),
        }
        rows = self.db.get(f"MEDIA_SECURITY_EVENTS_{cid}", [])
        if not isinstance(rows, list):
            rows = []
        rows.append(decision)
        self.db.set(f"MEDIA_SECURITY_EVENTS_{cid}", rows[-300:])
        return decision

    def media_events(self, chat_id, limit=50):
        rows = self.db.get(f"MEDIA_SECURITY_EVENTS_{self._cid(chat_id)}", [])
        if not isinstance(rows, list):
            return []
        return list(reversed(rows[-max(1, min(int(limit), 100)):]))

    def register_join(self, chat_id, user_id, name=""):
        cid, uid, now = self._cid(chat_id), self._uid(user_id), int(time.time())
        cfg = self.config(cid)
        was_raid_active = self.raid_state(cid)["active"]
        quarantine = self.db.get(f"QUARANTINE_{cid}", {})
        if cfg["quarantine"]["enabled"]:
            quarantine[uid] = {"joined_at": now, "messages": 0, "name": str(name)[:100]}
            self.db.set(f"QUARANTINE_{cid}", quarantine)

        joins = self.db.get(f"RAID_JOINS_{cid}", [])
        joins = [stamp for stamp in joins if now - int(stamp) <= cfg["raid"]["window_seconds"]]
        joins.append(now)
        self.db.set(f"RAID_JOINS_{cid}", joins[-200:])
        raid_triggered = cfg["raid"]["enabled"] and len(joins) >= cfg["raid"]["joins"]
        if raid_triggered:
            until = now + cfg["raid"]["lock_minutes"] * 60
            self.db.set(f"RAID_STATE_{cid}", {"active": True, "until": until, "joins": len(joins)})
        return {"quarantined": cfg["quarantine"]["enabled"], "raid_triggered": raid_triggered,
                "raid_activated": raid_triggered and not was_raid_active,
                "raid": self.raid_state(cid)}

    def raid_state(self, chat_id):
        cid, now = self._cid(chat_id), int(time.time())
        state = self.db.get(f"RAID_STATE_{cid}", {})
        if not isinstance(state, dict) or int(state.get("until", 0)) <= now:
            if state:
                self.db.set(f"RAID_STATE_{cid}", {})
            return {"active": False, "until": None, "joins": 0}
        return {"active": True, "until": state.get("until"), "joins": int(state.get("joins", 0))}

    def message_policy(self, chat_id, user_id, text, is_admin=False):
        cid, uid, now = self._cid(chat_id), self._uid(user_id), int(time.time())
        cfg = self.config(cid)
        result = {"delete": False, "reason": None, "quarantine": False, "rule": None, "warn": False, "signals": [], "mute_seconds": 0, "ban": False}
        if not is_admin:
            flood = cfg["flood_control"]
            if flood["enabled"]:
                key = f"FLOOD_ACTIVITY_{cid}_{uid}"
                activity = self.db.get(key, [])
                activity = [float(stamp) for stamp in activity if now - float(stamp) <= flood["window_seconds"]]
                activity.append(now)
                self.db.set(key, activity[-flood["messages"] * 2:])
                if len(activity) > flood["messages"]:
                    strike_key = f"FLOOD_STRIKES_{cid}"
                    strikes = self.db.get(strike_key, {})
                    strikes = strikes if isinstance(strikes, dict) else {}
                    strikes[uid] = int(strikes.get(uid, 0)) + 1
                    self.db.set(strike_key, strikes)
                    threshold = flood["strikes_before_ban"]
                    result.update({
                        "delete": flood["delete_messages"],
                        "reason": f"flood: más de {flood['messages']} mensajes en {flood['window_seconds']}s",
                        "mute_seconds": flood["mute_minutes"] * 60,
                        "ban": bool(threshold and strikes[uid] >= threshold),
                    })
                    self.db.set(key, [])
            limits = cfg["content_limits"]
            mention_count = len(re.findall(r"@\w+|tg://user\?id=\d+", text or "", re.I))
            emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF]", text or ""))
            letters = [char for char in (text or "") if char.isalpha()]
            upper_percent = round(sum(char.isupper() for char in letters) * 100 / len(letters)) if letters else 0
            if limits["enabled"]:
                if mention_count > limits["mentions"]:
                    result["signals"].append(f"{mention_count} menciones")
                if emoji_count > limits["emojis"]:
                    result["signals"].append(f"{emoji_count} emojis")
                if len(letters) >= 12 and upper_percent > limits["uppercase_percent"]:
                    result["signals"].append(f"{upper_percent}% mayúsculas")
                if result["signals"] and limits["action"] != "observe":
                    result["delete"] = True
                    result["warn"] = limits["action"] == "warn"
                    result["reason"] = "límites de contenido: " + ", ".join(result["signals"])

            slow = cfg["adaptive_slow"]
            if slow["enabled"] and not result["delete"]:
                activity = self.db.get(f"ADAPTIVE_ACTIVITY_{cid}", [])
                activity = [float(stamp) for stamp in activity if now - float(stamp) <= 60]
                activity.append(now)
                self.db.set(f"ADAPTIVE_ACTIVITY_{cid}", activity[-500:])
                pressure = min(1.0, len(activity) / slow["busy_messages"])
                delay = round(slow["base_seconds"] + pressure * (slow["max_seconds"] - slow["base_seconds"]))
                last_key = f"ADAPTIVE_LAST_{cid}_{uid}"
                last = float(self.db.get(last_key, 0) or 0)
                self.db.set(last_key, now)
                if last and now - last < delay:
                    result.update({"delete": True, "reason": f"modo lento adaptativo: espera {delay}s"})
        quarantine = self.db.get(f"QUARANTINE_{cid}", {})
        entry = quarantine.get(uid) if isinstance(quarantine, dict) else None
        if entry and not is_admin:
            expired = now - int(entry.get("joined_at", now)) >= cfg["quarantine"]["hours"] * 3600
            completed = int(entry.get("messages", 0)) >= cfg["quarantine"]["messages"]
            if expired or completed:
                quarantine.pop(uid, None)
            else:
                entry["messages"] = int(entry.get("messages", 0)) + 1
                quarantine[uid] = entry
                result["quarantine"] = True
                if cfg["quarantine"]["block_links"] and re.search(r"(?:https?://|t\.me/)", text or "", re.I):
                    result.update({"delete": True, "reason": "enlace durante la cuarentena"})
            self.db.set(f"QUARANTINE_{cid}", quarantine)

        rule = self.active_rule(cid)
        if rule and not is_admin:
            result["rule"] = rule
            if rule.get("action") == "admin_only":
                result.update({"delete": True, "reason": "regla programada: solo administradores"})
        return result

    def simulate_message(self, chat_id, text):
        """Simula límites sin alterar contadores, actividad ni sanciones."""
        cfg = self.config(chat_id)["content_limits"]
        mentions = len(re.findall(r"@\w+|tg://user\?id=\d+", text or "", re.I))
        emojis = len(re.findall(r"[\U0001F300-\U0001FAFF]", text or ""))
        letters = [char for char in (text or "") if char.isalpha()]
        uppercase = round(sum(char.isupper() for char in letters) * 100 / len(letters)) if letters else 0
        signals = []
        if mentions > cfg["mentions"]: signals.append(f"{mentions} menciones")
        if emojis > cfg["emojis"]: signals.append(f"{emojis} emojis")
        if len(letters) >= 12 and uppercase > cfg["uppercase_percent"]: signals.append(f"{uppercase}% mayúsculas")
        return {"would_match": bool(cfg["enabled"] and signals), "signals": signals,
                "action": cfg["action"] if signals else "allow",
                "metrics": {"mentions": mentions, "emojis": emojis, "uppercase_percent": uppercase}}

    def active_rule(self, chat_id, when=None):
        when = when or datetime.datetime.now()
        weekday, current = when.weekday(), when.strftime("%H:%M")
        for rule in self.config(chat_id)["rules"]:
            if not isinstance(rule, dict) or not rule.get("enabled", True):
                continue
            days = rule.get("days", list(range(7)))
            start, end = str(rule.get("start", "00:00")), str(rule.get("end", "23:59"))
            if weekday in days and (start <= current <= end if start <= end else current >= start or current <= end):
                return rule
        return None

    def create_report(self, chat_id, reporter_id, target_id, message_id=None, reason=""):
        cid = self._cid(chat_id)
        rows = self.db.get(f"GROUP_REPORTS_{cid}", [])
        if not isinstance(rows, list):
            rows = []
        now = datetime.datetime.now().isoformat()
        report = {
            "id": uuid.uuid4().hex[:12], "reporter_id": self._uid(reporter_id),
            "target_id": self._uid(target_id), "message_id": message_id,
            "reason": str(reason or "Reporte de usuario")[:500],
            "status": "pending", "created_at": now,
        }
        rows.append(report)
        self.db.set(f"GROUP_REPORTS_{cid}", rows[-500:])
        return report

    def resolve_report(self, chat_id, report_id, decision, admin_id):
        cid = self._cid(chat_id)
        rows = self.db.get(f"GROUP_REPORTS_{cid}", [])
        for row in rows:
            if row.get("id") == report_id and row.get("status") == "pending":
                row.update({"status": decision, "resolved_by": self._uid(admin_id),
                            "resolved_at": datetime.datetime.now().isoformat()})
                self.db.set(f"GROUP_REPORTS_{cid}", rows[-500:])
                return row
        return None

    def proposal(self, chat_id, target_id, action, reason, admin_id):
        cid = self._cid(chat_id)
        rows = self.db.get(f"CONSENSUS_{cid}", [])
        if not isinstance(rows, list):
            rows = []
        proposal = {
            "id": uuid.uuid4().hex[:12], "target_id": self._uid(target_id),
            "action": action, "reason": str(reason)[:500], "status": "pending",
            "votes": [self._uid(admin_id)], "created_at": datetime.datetime.now().isoformat(),
        }
        rows.append(proposal)
        self.db.set(f"CONSENSUS_{cid}", rows[-200:])
        return proposal

    def vote(self, chat_id, proposal_id, admin_id):
        cid = self._cid(chat_id)
        rows = self.db.get(f"CONSENSUS_{cid}", [])
        required = self.config(cid)["consensus"]["votes_required"]
        for row in rows:
            if row.get("id") != proposal_id or row.get("status") != "pending":
                continue
            votes = [str(value) for value in row.get("votes", [])]
            if self._uid(admin_id) not in votes:
                votes.append(self._uid(admin_id))
            row["votes"] = votes
            if len(votes) >= required:
                row["status"] = "approved"
                row["approved_at"] = datetime.datetime.now().isoformat()
            self.db.set(f"CONSENSUS_{cid}", rows[-200:])
            return row
        return None

    def roles(self, chat_id):
        rows = self.db.get(f"GROUP_ROLES_{self._cid(chat_id)}", {})
        return rows if isinstance(rows, dict) else {}

    def set_role(self, chat_id, user_id, role, expires_at=None):
        if role not in self.PURPOSES:
            return None
        rows = self.roles(chat_id)
        rows[self._uid(user_id)] = {"role": role, "expires_at": expires_at,
                                    "updated_at": datetime.datetime.now().isoformat()}
        self.db.set(f"GROUP_ROLES_{self._cid(chat_id)}", rows)
        return rows[self._uid(user_id)]

    def user_context(self, chat_id, user_id):
        cid, uid = self._cid(chat_id), self._uid(user_id)
        history = self.db.get(f"CHAT_HIST_{cid}", [])
        history = history if isinstance(history, list) else []
        messages = [row for row in history if str(row.get("uid")) == uid][-20:]
        events = self.db.get(f"SPAMEVENTS_{cid}", [])
        events = events if isinstance(events, list) else []
        reports = self.db.get(f"GROUP_REPORTS_{cid}", [])
        reports = reports if isinstance(reports, list) else []
        warns = self.db.get(f"WARNS_{cid}", {})
        bans = self.db.get(f"BANS_{cid}", {})
        quarantine = self.db.get(f"QUARANTINE_{cid}", {})
        warns = warns if isinstance(warns, dict) else {}
        bans = bans if isinstance(bans, dict) else {}
        quarantine = quarantine if isinstance(quarantine, dict) else {}
        return {
            "user_id": uid, "role": self.roles(cid).get(uid),
            "warnings": int(warns.get(uid, 0)),
            "locally_banned": uid in [str(value) for value in bans.get("users", [])],
            "messages": messages,
            "spam_events": [row for row in events if str(row.get("user_id")) == uid][-20:],
            "reports": [row for row in reports if str(row.get("target_id")) == uid][-20:],
            "quarantine": quarantine.get(uid),
        }

    def summary(self, chat_id):
        cid = self._cid(chat_id)
        history = self.db.get(f"CHAT_HIST_{cid}", [])
        history = history[-500:] if isinstance(history, list) else []
        texts = [str(row.get("text", "")) for row in history if row.get("text")]
        words = Counter(
            word for text in texts for word in re.findall(r"[a-záéíóúñ]{4,}", text.lower())
            if word not in {"para", "como", "este", "esta", "pero", "porque", "desde", "sobre"}
        )
        reports = self.db.get(f"GROUP_REPORTS_{cid}", [])
        return {
            "generated_at": datetime.datetime.now().isoformat(),
            "messages": len(texts), "participants": len(set(str(row.get("uid")) for row in history if row.get("uid"))),
            "topics": [word for word, _ in words.most_common(8)],
            "questions": [text[:250] for text in texts if text.strip().endswith("?")][-10:],
            "reports": len(reports),
            "moderation_events": len(self.db.get(f"SPAMEVENTS_{cid}", [])),
        }

    def templates(self, chat_id):
        rows = self.db.get("GROUP_TEMPLATES", [])
        return rows if isinstance(rows, list) else []

    def save_template(self, chat_id, name):
        rows = self.templates(chat_id)
        template = {
            "id": uuid.uuid4().hex[:12], "name": str(name)[:80],
            "source_chat_id": self._cid(chat_id),
            "config": self.config(chat_id),
            "badwords": self.db.get(f"BADWORDS_{self._cid(chat_id)}", {}),
            "spam_config": self.db.get(f"SPAMCFG_{self._cid(chat_id)}", {}),
            "created_at": datetime.datetime.now().isoformat(),
        }
        rows.append(template)
        self.db.set("GROUP_TEMPLATES", rows[-50:])
        return template

    def apply_template(self, chat_id, template_id):
        template = next((row for row in self.templates(chat_id) if row.get("id") == template_id), None)
        if not template:
            return None
        cid = self._cid(chat_id)
        self.db.set(f"GROUPSUITE_{cid}", template.get("config", {}))
        self.db.set(f"BADWORDS_{cid}", template.get("badwords", {}))
        self.db.set(f"SPAMCFG_{cid}", template.get("spam_config", {}))
        return template

    def snapshot(self, chat_id):
        cid = self._cid(chat_id)
        reports = self.db.get(f"GROUP_REPORTS_{cid}", [])
        consensus = self.db.get(f"CONSENSUS_{cid}", [])
        quarantine = self.db.get(f"QUARANTINE_{cid}", {})
        return {
            "config": self.config(cid), "raid": self.raid_state(cid),
            "quarantine": quarantine if isinstance(quarantine, dict) else {},
            "reports": list(reversed(reports[-100:])) if isinstance(reports, list) else [],
            "consensus": list(reversed(consensus[-100:])) if isinstance(consensus, list) else [],
            "roles": self.roles(cid), "templates": self.templates(cid),
            "media_events": self.media_events(cid),
            "bot_interactions": list(reversed(self.db.get(f"BOT_INTERACTION_EVENTS_{cid}", [])[-100:])),
        }
