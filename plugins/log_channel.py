from moon_multibot import add_web_log
import os

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Log Channel
    Envía logs de auditoría a un canal específico configurado para el grupo.
    
    Comandos:
    /setlog <channel_id>
    /unsetlog
    """
    
    if str(rank).lower() not in ["admin", "master"]:
        return False
        
    t_lower = text.lower()
    
    if t_lower.startswith("/setlog "):
        parts = t_lower.split(" ")
        if len(parts) == 2:
            log_channel = parts[1]
            # Validar y guardar
            settings = bot.db.get("GLOBAL_SETTINGS", {})
            log_mapping = settings.get("log_channels", {})
            log_mapping[str(cid)] = log_channel
            settings["log_channels"] = log_mapping
            bot.db.set("GLOBAL_SETTINGS", settings)
            
            bot.send_msg(cid, f"✅ Canal de auditoría configurado: `{log_channel}`")
            bot.send_msg(log_channel, f"🔔 Este canal ha sido configurado como registro de auditoría para el chat `{cid}`.")
        else:
            bot.send_msg(cid, "❌ Uso: `/setlog <channel_id>`")
        return True
        
    if t_lower == "/unsetlog":
        settings = bot.db.get("GLOBAL_SETTINGS", {})
        log_mapping = settings.get("log_channels", {})
        if str(cid) in log_mapping:
            del log_mapping[str(cid)]
            settings["log_channels"] = log_mapping
            bot.db.set("GLOBAL_SETTINGS", settings)
            bot.send_msg(cid, "✅ Canal de auditoría desvinculado.")
        else:
            bot.send_msg(cid, "ℹ️ Este chat no tiene canal de auditoría configurado.")
        return True
        
    return False

# Nota: Para que el Log Channel funcione a plenitud, otros plugins (como Warns o Moderation) 
# deben importar o enviar directamente mensajes al log_channel configurado leyendo de GLOBAL_SETTINGS.
