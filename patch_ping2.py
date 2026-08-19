with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

ping_route = """@app.route("/api/admin/telegram_ping", methods=["GET"])
def telegram_ping():
    try:
        if not active_bots:
            return jsonify({"status": "error", "message": "No hay bots activos en active_bots."}), 500
        bot = active_bots[0]
        res = requests.get(f"https://api.telegram.org/bot{bot.token}/getMe", timeout=10)
        data = res.json()
        if data.get("ok"):
            return jsonify({
                "status": "ok", 
                "bot_username": data["result"]["username"],
                "active_bots_count": len(active_bots),
                "is_patched": getattr(bot, "_patched_for_router", False)
            }), 200
        else:
            return jsonify({"status": "error", "telegram_error": data}), 400
    except Exception as e:
        return jsonify({"status": "exception", "message": str(e)}), 500
"""

content = content.replace('if __name__ == "__main__":', ping_route + '\nif __name__ == "__main__":')

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
