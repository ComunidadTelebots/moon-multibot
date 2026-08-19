from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Purge & Nuke (Limpieza Masiva) - RC
    Comandos (Admin):
    /del - Borra el mensaje al que se responde.
    /purge - (Simulado) En un bot real con acceso completo a los IDs de mensaje, 
             iteraría desde el ID del reply hasta el actual borrándolos en lote.
    """
    
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    
    if t_lower == "/del":
        # En una API de Telegram real, usaríamos el `reply_to_message.message_id`
        # Como este framework actual parsea texto plano para el core, usaremos un mock 
        # para enviar la orden y registrar el log.
        bot.send_msg(cid, "🗑️ Comando `/del` recibido. (Requiere ID de mensaje para ejecutar en API).")
        add_web_log("INFO", f"Comando /del usado en {cid}")
        return True
        
    if t_lower == "/purge":
        bot.send_msg(cid, "🧹 **Purge Iniciado**\nEliminando mensajes... (Simulación: en producción requiere iterador de message_id).")
        add_web_log("WARNING", f"Comando /purge usado en {cid} por {uid}")
        return True

    return False
