"""Registro local y auditable de incidentes por grupo."""

import datetime

PLUGIN_INFO = {"name": "Registro de incidentes", "version": "1.0.0", "commands": ["/incident", "/incidents"]}


def handle_command(bot, cid, uid, text, rank):
    low = text.strip().lower()
    if not (low.startswith("/incident") or low.startswith("/incidente")):
        return False
    if str(rank).lower() not in ("admin", "master"):
        bot.send_msg(cid, "Solo los administradores pueden gestionar incidentes.")
        return True
    from moon_multibot import db
    key = f"PLUGIN_INCIDENTS_{cid}"
    rows = db.get(key, [])
    rows = rows if isinstance(rows, list) else []
    if low in ("/incidents", "/incidentes", "/incident list", "/incidente lista"):
        recent = rows[-10:]
        body = "\n".join(f"{item['id']}. {item['text']} ({item['created_at']})" for item in recent)
        bot.send_msg(cid, "Incidentes recientes:\n" + (body or "No hay incidentes."))
        return True
    payload = text.split(maxsplit=1)
    if len(payload) < 2:
        bot.send_msg(cid, "Uso: /incident <descripcion> o /incidents")
        return True
    next_id = max((int(item.get("id", 0)) for item in rows if isinstance(item, dict)), default=0) + 1
    rows.append({"id": next_id, "text": payload[1][:500], "created_by": str(uid),
                 "created_at": datetime.datetime.now().isoformat(timespec="minutes")})
    db.set(key, rows[-200:])
    bot.send_msg(cid, f"Incidente #{rows[-1]['id']} registrado.")
    return True
