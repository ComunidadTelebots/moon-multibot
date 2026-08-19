"""Plantillas seguras para activar configuraciones habituales de GroupSuite."""

PLUGIN_INFO = {"name": "Plantillas de moderacion", "version": "1.0.0", "commands": ["/ruletemplate"]}

TEMPLATES = {
    "estricto": {"quarantine": {"enabled": True, "hours": 24, "messages": 5}, "raid": {"enabled": True, "joins": 6}, "content_limits": {"enabled": True, "mentions": 4, "emojis": 15, "uppercase_percent": 65, "action": "warn"}},
    "equilibrado": {"quarantine": {"enabled": True, "hours": 12, "messages": 3}, "raid": {"enabled": True, "joins": 10}, "content_limits": {"enabled": True, "mentions": 7, "emojis": 25, "uppercase_percent": 80, "action": "observe"}},
    "comunidad": {"quarantine": {"enabled": False}, "raid": {"enabled": True, "joins": 15}, "welcome": {"enabled": True}, "content_limits": {"enabled": False}},
}


def handle_command(bot, cid, uid, text, rank):
    low = text.strip().lower()
    if not (low.startswith("/ruletemplate") or low.startswith("/plantillareglas")):
        return False
    if str(rank).lower() not in ("admin", "master"):
        bot.send_msg(cid, "Solo los administradores pueden aplicar plantillas.")
        return True
    name = text.strip().split(maxsplit=1)[1].lower() if len(text.strip().split(maxsplit=1)) > 1 else ""
    if name not in TEMPLATES:
        bot.send_msg(cid, "Plantillas disponibles: estricto, equilibrado, comunidad.")
        return True
    from moon_multibot import db
    from group_suite import GroupSuite
    GroupSuite(db).save_config(cid, TEMPLATES[name])
    bot.send_msg(cid, f"Plantilla '{name}' aplicada correctamente.")
    return True
