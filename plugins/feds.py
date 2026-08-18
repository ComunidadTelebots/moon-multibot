from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Federaciones (Feds) - ALFA
    Baneos sincronizados entre múltiples grupos.
    
    Comandos (Admin):
    /newfed <Nombre>
    /delfed <fed_id>
    /joinfed <fed_id>
    /leavefed <fed_id>
    /fban <user_id> [motivo]
    /unfban <user_id>
    """
    
    if str(rank).lower() not in ["admin", "master"] or not text.startswith("/"):
        return False
        
    t_lower = text.lower()
    parts = text.split(" ")
    
    # Base de datos global para Federaciones
    # Formato: {"fed_id": {"name": "...", "creator": uid, "chats": [cid1, cid2], "banned_users": {uid1: "motivo"}}}
    feds_db = bot.db.get("GLOBAL_FEDS", {})
    
    if t_lower.startswith("/newfed "):
        name = text[8:].strip()
        import uuid
        fed_id = str(uuid.uuid4())[:8] # Generar ID corto
        feds_db[fed_id] = {
            "name": name,
            "creator": str(uid),
            "chats": [str(cid)],
            "banned_users": {}
        }
        bot.db.set("GLOBAL_FEDS", feds_db)
        bot.send_msg(cid, f"🌐 **Federación creada exitosamente**\n• Nombre: `{name}`\n• ID: `{fed_id}`\n\nEste chat ha sido unido automáticamente. Usa `/joinfed {fed_id}` en otros grupos.")
        add_web_log("SUCCESS", f"Fed '{name}' ({fed_id}) creada por {uid}")
        return True
        
    if t_lower.startswith("/joinfed "):
        if len(parts) == 2:
            fed_id = parts[1]
            if fed_id in feds_db:
                if str(cid) not in feds_db[fed_id]["chats"]:
                    feds_db[fed_id]["chats"].append(str(cid))
                    bot.db.set("GLOBAL_FEDS", feds_db)
                    bot.send_msg(cid, f"✅ El chat se ha unido a la Federación `{feds_db[fed_id]['name']}`.")
                else:
                    bot.send_msg(cid, "ℹ️ Este chat ya pertenece a esta Federación.")
            else:
                bot.send_msg(cid, "❌ Federación no encontrada.")
        return True
        
    if t_lower.startswith("/leavefed "):
        if len(parts) == 2:
            fed_id = parts[1]
            if fed_id in feds_db and str(cid) in feds_db[fed_id]["chats"]:
                feds_db[fed_id]["chats"].remove(str(cid))
                bot.db.set("GLOBAL_FEDS", feds_db)
                bot.send_msg(cid, f"🚪 El chat ha abandonado la Federación `{feds_db[fed_id]['name']}`.")
            else:
                bot.send_msg(cid, "❌ No se pudo abandonar (ID incorrecto o no estás unido).")
        return True
        
    if t_lower.startswith("/fban "):
        if len(parts) >= 2:
            target_uid = parts[1]
            reason = " ".join(parts[2:]) if len(parts) > 2 else "Sin motivo"
            
            # Buscar a qué Feds pertenece este grupo
            active_feds = [fid for fid, f in feds_db.items() if str(cid) in f["chats"]]
            
            if not active_feds:
                bot.send_msg(cid, "❌ Este chat no pertenece a ninguna Federación. Usa `/joinfed` primero.")
                return True
                
            for fid in active_feds:
                # FBaneo a nivel lógico
                feds_db[fid]["banned_users"][target_uid] = reason
                
                # Opcional en ALFA: Iterar por todos los chats de la fed e intentar banear proactivamente
                # Aquí lo dejamos como registro centralizado para la db, el chequeo pasivo lo hará al hablar
            
            bot.db.set("GLOBAL_FEDS", feds_db)
            bot.send_msg(cid, f"⛔ **F-Ban aplicado**\nUsuario `{target_uid}` ha sido baneado en {len(active_feds)} federaciones.\nMotivo: _{reason}_")
            add_web_log("WARNING", f"F-Ban a {target_uid} en {len(active_feds)} federaciones")
        return True
        
    if t_lower.startswith("/unfban "):
        if len(parts) >= 2:
            target_uid = parts[1]
            active_feds = [fid for fid, f in feds_db.items() if str(cid) in f["chats"]]
            
            removed = 0
            for fid in active_feds:
                if target_uid in feds_db[fid]["banned_users"]:
                    del feds_db[fid]["banned_users"][target_uid]
                    removed += 1
                    
            bot.db.set("GLOBAL_FEDS", feds_db)
            bot.send_msg(cid, f"✅ **Un-F-Ban aplicado**\nUsuario `{target_uid}` desbaneado en {removed} federaciones.")
        return True
        
    # Comprobación pasiva (interceptar F-Baneados que intentan hablar o unirse)
    # Si este grupo pertenece a Feds, chequear si el usuario actual está en la blacklist global
    active_feds = [fid for fid, f in feds_db.items() if str(cid) in f["chats"]]
    for fid in active_feds:
        if str(uid) in feds_db[fid]["banned_users"]:
            reason = feds_db[fid]["banned_users"][str(uid)]
            # Eliminar mensaje y banear localmente
            try:
                bot.api_call("banChatMember", {"chat_id": cid, "user_id": uid})
                bot.send_msg(cid, f"🛡️ **Protección de Federación**\nEl usuario @{uid} ha sido expulsado automáticamente por estar baneado en la Fed `{feds_db[fid]['name']}`.\nMotivo: _{reason}_")
            except:
                pass
            return True # Bloqueamos

    return False
