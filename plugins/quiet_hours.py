"""Configura una franja silenciosa que otras automatizaciones pueden consultar."""

import re

from group_suite import GroupSuite
from quiet_hours_policy import decide_quiet_hours

PLUGIN_INFO = {"name": "Horario silencioso", "version": "1.0.0", "commands": ["/quiethours"]}


def handle_command(bot, cid, uid, text, rank):
    low = text.strip().lower()
    if not (low.startswith("/quiethours") or low.startswith("/horariosilencioso")):
        return False
    if str(rank).lower() not in ("admin", "master"):
        bot.send_msg(cid, "Solo los administradores pueden cambiar el horario silencioso.")
        return True
    from moon_multibot import db
    suite = GroupSuite(db)
    parts = text.strip().split(maxsplit=1)
    if len(parts) == 1:
        cfg = suite.config(cid)["quiet_hours"]
        decision = decide_quiet_hours(cfg)
        bot.send_msg(cid, f"Horario silencioso: {cfg['start']} - {cfg['end']} ({'reteniendo automatizaciones' if decision['held'] else 'fuera de franja'}). Próximo cambio: {decision.get('next_transition') or 'sin programar'}.")
        return True
    value = parts[1].strip().lower()
    if value in ("off", "desactivar"):
        suite.save_config(cid, {"quiet_hours": {"enabled": False}}, actor=uid, source="telegram-command")
        bot.send_msg(cid, "Horario silencioso desactivado.")
        return True
    if value.startswith("allow "):
        categories = [item.strip().lower() for item in value[6:].split(",") if item.strip()]
        try:
            suite.save_config(cid, {"quiet_hours": {"allowed_categories": categories}}, actor=uid, source="telegram-command")
            bot.send_msg(cid, "Excepciones actualizadas: " + ", ".join(categories))
        except ValueError as error:
            bot.send_msg(cid, f"Configuración no válida: {error}")
        return True
    parts = value.split()
    window, timezone = parts[0], parts[1] if len(parts) > 1 else "Europe/Madrid"
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)", window)
    if not match:
        bot.send_msg(cid, "Uso: /quiethours 23:00-07:00 o /quiethours off")
        return True
    start, end = window.split("-")
    try:
        suite.save_config(cid, {"quiet_hours": {"enabled": True, "start": start, "end": end, "timezone": timezone}}, actor=uid, source="telegram-command")
    except ValueError as error:
        bot.send_msg(cid, f"Configuración no válida: {error}")
        return True
    bot.send_msg(cid, f"Horario silencioso activado de {start} a {end}.")
    return True
