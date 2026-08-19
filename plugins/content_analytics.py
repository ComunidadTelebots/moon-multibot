from moon_multibot import add_web_log
from collections import Counter
import re

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin Analíticas de Contenido (ALFA)
    Comando: /stats
    Recopila y muestra estadísticas básicas de uso de un chat.
    """
    
    # 1. Registro pasivo de palabras
    # En un bot real esto podría ser un problema de memoria, por eso es ALFA
    stats_db = bot.db.get(f"STATS_{cid}", {"msgs_count": 0, "users": {}, "words": []})
    
    # Registrar mensaje
    stats_db["msgs_count"] += 1
    
    # Contar usuario
    uid_str = str(uid)
    stats_db["users"][uid_str] = stats_db["users"].get(uid_str, 0) + 1
    
    # Extraer palabras limpias
    if text and not text.startswith("/"):
        words = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}\b', text.lower())
        # Evitar sobrecargar la BD (límite de 500 palabras)
        stats_db["words"].extend(words)
        if len(stats_db["words"]) > 1000:
            stats_db["words"] = stats_db["words"][-1000:]
            
    bot.db.set(f"STATS_{cid}", stats_db)
    
    # 2. Comando para ver las estadísticas
    if text.lower() == "/stats" and str(rank).lower() in ["admin", "master"]:
        total_msgs = stats_db["msgs_count"]
        
        # Calcular usuarios más activos
        top_users = sorted(stats_db["users"].items(), key=lambda item: item[1], reverse=True)[:3]
        
        # Calcular palabras más frecuentes
        word_counts = Counter(stats_db["words"])
        top_words = word_counts.most_common(5)
        
        msg = f"📊 **Analíticas de Contenido del Grupo**\n\n"
        msg += f"• **Total de mensajes:** `{total_msgs}`\n"
        
        msg += "\n🏆 **Usuarios más activos:**\n"
        for i, (u, count) in enumerate(top_users):
            msg += f" {i+1}. @{u} ({count} msgs)\n"
            
        msg += "\n💬 **Temas recurrentes (Palabras clave):**\n"
        for w, c in top_words:
            msg += f" • `{w}` ({c} veces)\n"
            
        bot.send_msg(cid, msg)
        add_web_log("INFO", f"Reporte de stats generado en {cid}")
        return True

    return False
