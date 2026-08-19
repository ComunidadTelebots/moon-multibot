import time
from collections import defaultdict
from moon_multibot import add_web_log

# Historial de mensajes por usuario (chat_id -> user_id -> [timestamps])
flood_history = defaultdict(lambda: defaultdict(list))

FLOOD_LIMIT = 5  # mensajes
FLOOD_TIME = 5   # segundos

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Anti-Flood
    Bloquea a usuarios que envíen más de N mensajes en T segundos.
    """
    if rank in ["master", "admin"]:
        return False  # Los admins no tienen restricción de flood
        
    # Limpiar historial viejo de este usuario
    current_time = time.time()
    history = flood_history[cid][uid]
    
    # Mantener solo los mensajes dentro del margen de tiempo
    history = [t for t in history if current_time - t <= FLOOD_TIME]
    
    # Añadir mensaje actual
    history.append(current_time)
    flood_history[cid][uid] = history
    
    if len(history) > FLOOD_LIMIT:
        # 1. Avisar
        bot.send_msg(cid, f"⚠️ ¡Alto ahí! @{uid} estás enviando mensajes demasiado rápido. Has sido silenciado temporalmente por Anti-Flood.")
        
        # 2. Silenciar / Eliminar
        # Telegram API para restringir: restrictChatMember
        try:
            bot.api_call("restrictChatMember", {
                "chat_id": cid,
                "user_id": uid,
                "permissions": {"can_send_messages": False},
                "until_date": int(current_time) + 300 # 5 minutos
            })
            add_web_log("WARNING", f"Anti-Flood activado para {uid} en el chat {cid}")
        except Exception as e:
            add_web_log("ERROR", f"Error aplicando Anti-Flood a {uid}: {str(e)}")
            
        # 3. Limpiar historial para no spamear advertencias
        flood_history[cid][uid] = []
        return True # Evitar que otros plugins procesen este mensaje
        
    return False
