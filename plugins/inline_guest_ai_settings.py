"""
Plugin para gestionar configuración de IA en modo Inline y Guest
Comandos:
- /ia_stats: Ver estadísticas de uso de IA
- /ia_set_default <ollama|gemini|hybrid>: Establecer IA por defecto
- /ia_info: Información del sistema IA actual
"""

def handle_command(bot, cid, uid, text, rank):
    """Maneja comandos de configuración de IA para inline y guest."""
    
    t_lower = text.lower()
    
    # Comando: /ia_stats - Ver estadísticas de IA
    if t_lower.startswith("/ia_stats"):
        if rank != "master":
            bot.send_msg(cid, "❌ Solo master puede ver estadísticas")
            return True
        
        try:
            stats = bot.ia_nativa.get_ai_statistics()
            
            summary = stats["summary"]
            distribution = stats["ai_distribution"]
            results = stats["results"]
            
            message = (
                f"📊 *Estadísticas de IA (Inline + Guest)*\n\n"
                f"*Resumen General:*\n"
                f"• Total de solicitudes: {summary['total_requests']}\n"
                f"• Inline: {summary['inline_requests']}\n"
                f"• Guest: {summary['guest_requests']}\n"
                f"• Tasa éxito: {summary['success_rate_percent']}%\n"
                f"• Tiempo promedio: {summary['avg_response_time_ms']}ms\n\n"
                f"*Distribución de IA:*\n"
                f"• Ollama: {distribution['ollama']}\n"
                f"• Gemini: {distribution['gemini']}\n"
                f"• Híbrida: {distribution['hybrid']}\n\n"
                f"*Resultados:*\n"
                f"• ✅ Exitosas: {results['success']}\n"
                f"• ❌ Fallidas: {results['failed']}\n"
            )
            
            # Mostrar últimos eventos
            recent = stats.get("recent_events", [])
            if recent:
                message += f"\n*Últimos 5 eventos:*\n"
                for event in recent[-5:]:
                    time_str = event["time"]
                    mode = "📱" if event["mode"] == "inline" else "👤"
                    ai = event["ai_used"]
                    status = "✅" if event["success"] else "❌"
                    message += f"{status} {mode} [{ai}] {time_str}\n"
            
            bot.send_msg(cid, message, parse_mode="Markdown")
        except Exception as e:
            bot.send_msg(cid, f"❌ Error: {str(e)}")
        
        return True
    
    # Comando: /ia_set_default - Cambiar IA por defecto
    elif t_lower.startswith("/ia_set_default"):
        if rank != "master":
            bot.send_msg(cid, "❌ Solo master puede cambiar configuración")
            return True
        
        parts = text.split()
        if len(parts) < 2:
            bot.send_msg(cid, 
                "❌ Uso: /ia_set_default <ollama|gemini|hybrid>\n"
                "Ejemplo: /ia_set_default hybrid"
            )
            return True
        
        ai_mode = parts[1].lower()
        if ai_mode not in ["ollama", "gemini", "hybrid"]:
            bot.send_msg(cid, 
                "❌ IA válidas: ollama, gemini, hybrid\n"
                "Ejemplo: /ia_set_default hybrid"
            )
            return True
        
        try:
            settings = bot.db.get("GLOBAL_SETTINGS", {})
            old_mode = settings.get("default_ai_mode", "hybrid")
            settings["default_ai_mode"] = ai_mode
            bot.db.set("GLOBAL_SETTINGS", settings)
            
            from moon_multibot import add_web_log
            add_web_log("INFO", f"IA por defecto cambiada de {old_mode} a {ai_mode}")
            
            message = (
                f"✅ *IA por defecto actualizada*\n\n"
                f"• Anterior: {old_mode}\n"
                f"• Nueva: {ai_mode}\n\n"
                f"Los nuevos queries inline y guest usarán *{ai_mode}*"
            )
            bot.send_msg(cid, message, parse_mode="Markdown")
        except Exception as e:
            bot.send_msg(cid, f"❌ Error: {str(e)}")
        
        return True
    
    # Comando: /ia_info - Información del sistema IA
    elif t_lower.startswith("/ia_info"):
        if rank not in ["admin", "master"]:
            bot.send_msg(cid, "❌ Solo admin/master pueden ver esta información")
            return True
        
        try:
            settings = bot.db.get("GLOBAL_SETTINGS", {})
            default_ai = settings.get("default_ai_mode", "hybrid")
            
            # Información del sistema
            import os
            from core.config import GEMINI_API_KEY, OLLAMA_MODEL, USE_EXTERNAL_LLM
            
            gemini_status = "✅ Configurado" if GEMINI_API_KEY else "❌ No configurado"
            ollama_status = f"✅ {OLLAMA_MODEL}"
            external_llm_status = "✅ Habilitado" if USE_EXTERNAL_LLM else "❌ Deshabilitado"
            
            message = (
                f"🧠 *Configuración de IA del Sistema*\n\n"
                f"*IA por Defecto:*\n"
                f"• {default_ai.upper()}\n\n"
                f"*Modelos Disponibles:*\n"
                f"• Ollama: {ollama_status}\n"
                f"• Gemini: {gemini_status}\n"
                f"• LLM Externo: {external_llm_status}\n\n"
                f"*Modo de Operación:*\n"
                f"• El sistema usa la IA seleccionada por defecto\n"
                f"• Los usuarios pueden usar /ollama, /gemini o /hybrid en sus queries\n"
                f"• Las respuestas son registradas para estadísticas\n"
            )
            
            bot.send_msg(cid, message, parse_mode="Markdown")
        except Exception as e:
            bot.send_msg(cid, f"❌ Error: {str(e)}")
        
        return True
    
    return False
