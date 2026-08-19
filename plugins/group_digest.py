"""Resumen local de actividad sin enviar contenido a servicios externos."""

from collections import Counter

PLUGIN_INFO = {"name": "Resumen del grupo", "version": "1.0.0", "commands": ["/digest"]}


def handle_command(bot, cid, uid, text, rank):
    if text.strip().lower() not in ("/digest", "/resumen"):
        return False
    if str(rank).lower() not in ("admin", "master"):
        bot.send_msg(cid, "Solo los administradores pueden generar el resumen.")
        return True
    from moon_multibot import db, global_chat_history
    history = global_chat_history.get(str(cid)) or db.get(f"CHAT_HIST_{cid}", []) or []
    recent = [row for row in history[-200:] if isinstance(row, dict)]
    senders = Counter(str(row.get("sender") or row.get("uid") or "desconocido") for row in recent)
    top = ", ".join(f"{name} ({count})" for name, count in senders.most_common(5)) or "sin actividad"
    media = sum(bool(row.get("media")) for row in recent)
    bot.send_msg(cid, f"Resumen de las ultimas {len(recent)} entradas\nParticipantes principales: {top}\nContenido multimedia: {media}")
    return True
