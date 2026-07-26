"""Configura una franja silenciosa que otras automatizaciones pueden consultar."""

import re

PLUGIN_INFO = {"name": "Horario silencioso", "version": "1.0.0", "commands": ["/quiethours"]}


def handle_command(bot, cid, uid, text, rank):
    low = text.strip().lower()
    if not (low.startswith("/quiethours") or low.startswith("/horariosilencioso")):
        return False
    if str(rank).lower() not in ("admin", "master"):
        bot.send_msg(cid, "Solo los administradores pueden cambiar el horario silencioso.")
        return True
    from moon_multibot import db
    key = f"QUIET_HOURS_{cid}"
    parts = text.strip().split(maxsplit=1)
    if len(parts) == 1:
        cfg = db.get(key, {}) or {}
        bot.send_msg(cid, f"Horario silencioso: {cfg.get('start', '--:--')} - {cfg.get('end', '--:--')} ({'activo' if cfg.get('enabled') else 'inactivo'}).")
        return True
    value = parts[1].strip().lower()
    if value in ("off", "desactivar"):
        db.set(key, {"enabled": False})
        bot.send_msg(cid, "Horario silencioso desactivado.")
        return True
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)", value)
    if not match:
        bot.send_msg(cid, "Uso: /quiethours 23:00-07:00 o /quiethours off")
        return True
    start, end = value.split("-")
    db.set(key, {"enabled": True, "start": start, "end": end, "timezone": "group"})
    bot.send_msg(cid, f"Horario silencioso activado de {start} a {end}.")
    return True
