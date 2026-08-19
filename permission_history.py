"""Historial persistente y deduplicado de permisos efectivos de bots."""

import datetime
import time


def record_permission_snapshot(db, chat_id, bot, status, chat_type, missing, actor):
    key = f"BOT_PERMISSION_HISTORY_{chat_id}"
    stored = db.get(key, [])
    rows = list(stored) if isinstance(stored, list) else []
    bot_id = str(getattr(bot, "bot_id", ""))
    missing_names = sorted(str(item.get("permission")) for item in missing if item.get("permission"))
    previous = next((row for row in reversed(rows) if str(row.get("bot_id")) == bot_id), None)
    signature = {"status": str(status), "chat_type": str(chat_type), "missing": missing_names}
    changed = not previous or previous.get("signature") != signature
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if changed:
        rows.append({
            "id": f"perm-{int(time.time() * 1000)}-{bot_id}",
            "bot_id": bot_id,
            "bot_username": str(getattr(bot, "bot_username", "MoonBot"))[:100],
            "actor": str(actor or "system")[:100],
            "detected_at": now,
            "healthy": not missing,
            "status": str(status),
            "chat_type": str(chat_type),
            "missing": [{"permission": str(item.get("permission"))[:80],
                         "label": str(item.get("label"))[:120]} for item in missing],
            "signature": signature,
        })
        db.set(key, rows[-100:])
    db.set(f"BOT_PERMISSION_LAST_CHECK_{chat_id}", now)
    return list(reversed(rows[-50:])), changed
