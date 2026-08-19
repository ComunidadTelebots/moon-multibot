import random
from moon_multibot import add_web_log

def handle_command(bot, cid, uid, text, rank):
    """
    Plugin de Economía: MoonCoins
    Añade un sistema de economía donde los usuarios ganan monedas por hablar
    y pueden gastarlas en la tienda del grupo.
    
    Comandos:
    /wallet : Ver saldo
    /daily : Recompensa diaria
    /shop : Ver tienda
    /buy <item> : Comprar objeto
    """
    
    user_db_key = f"USER_ECON_{cid}_{uid}"
    user_data = bot.db.get(user_db_key, {"coins": 0, "last_daily": 0, "inventory": []})
    
    # 1. Ganar monedas pasivamente por hablar (Probabilidad 20% de ganar 1-3 monedas)
    if text and not text.startswith("/") and random.random() < 0.2:
        earned = random.randint(1, 3)
        user_data["coins"] += earned
        bot.db.set(user_db_key, user_data)
        
    # 2. Comandos de usuario
    if text.startswith("/wallet"):
        bot.send_msg(cid, f"💰 **Tu Billetera:**\n\n🪙 MoonCoins: `{user_data['coins']}`\n🎒 Objetos: `{len(user_data['inventory'])}`")
        return True
        
    if text.startswith("/shop"):
        shop = "🛒 **Tienda del Grupo** 🛒\n\n"
        shop += "1. `Título VIP` - 500 MoonCoins\n"
        shop += "2. `Inmunidad al Flood (1h)` - 1000 MoonCoins\n\n"
        shop += "Usa `/buy <nombre_item>` para comprar."
        bot.send_msg(cid, shop)
        return True
        
    if text.startswith("/buy "):
        item = text[5:].strip().lower()
        if item == "titulo vip":
            if user_data["coins"] >= 500:
                user_data["coins"] -= 500
                user_data["inventory"].append("Título VIP")
                bot.db.set(user_db_key, user_data)
                bot.send_msg(cid, f"✅ Has comprado **Título VIP**. Te quedan {user_data['coins']} MoonCoins.")
                add_web_log("INFO", f"Usuario {uid} compró Título VIP en {cid}")
            else:
                bot.send_msg(cid, "❌ No tienes suficientes MoonCoins.")
        else:
            bot.send_msg(cid, "❌ Objeto no encontrado en la tienda.")
        return True

    return False
