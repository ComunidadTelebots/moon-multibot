"""Diagnostico rapido de permisos y estado del grupo."""

PLUGIN_INFO = {"name": "Salud del grupo", "version": "1.0.0", "commands": ["/grouphealth"]}


def handle_command(bot, cid, uid, text, rank):
    if text.strip().lower() not in ("/grouphealth", "/saludgrupo"):
        return False
    if str(rank).lower() not in ("admin", "master"):
        bot.send_msg(cid, "Esta comprobacion solo esta disponible para administradores.")
        return True
    member = bot.api_call("getChatMember", {"chat_id": cid, "user_id": bot.bot_id}, silent=True)
    result = member.get("result", {}) if isinstance(member, dict) else {}
    required = {
        "can_delete_messages": "eliminar mensajes",
        "can_restrict_members": "restringir miembros",
        "can_invite_users": "aprobar usuarios",
        "can_pin_messages": "fijar mensajes",
    }
    missing = [] if result.get("status") == "creator" else [label for key, label in required.items() if not result.get(key)]
    status = "Correcto" if not missing else "Requiere atencion"
    detail = "Todos los permisos esenciales estan disponibles." if not missing else "Faltan: " + ", ".join(missing)
    bot.send_msg(cid, f"Salud del grupo: {status}\n{detail}")
    return True
