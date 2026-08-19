"""Comando informativo; la ejecución segura vive en el flujo de mensajes de voz."""

def handle_command(bot, cid, uid, text, rank):
    t_lower = text.lower()
    
    if t_lower.startswith("/transcribe"):
        bot.send_msg(cid, "Activa la transcripción con consentimiento en el panel del grupo y envía una nota de voz. Por seguridad no se aceptan file_id manuales.")
        return True
    
    return False
