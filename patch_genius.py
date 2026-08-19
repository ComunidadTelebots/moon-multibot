with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

webhook_route = """
@app.route("/api/telegram/webhook/<token>", methods=["POST"])
def telegram_webhook(token):
    from flask import request
    update = request.json
    if not update: return "OK", 200
    for bot in active_bots.values():
        if bot.token == token:
            try:
                import queue
                if not hasattr(bot, "router_queue"):
                    bot.router_queue = queue.Queue()
                bot.router_queue.put(update)
            except Exception as e:
                pass
            return "OK", 200
    return "Not Found", 404
"""
if "def telegram_webhook" not in content:
    idx = content.find("@app.route(\"/api/internal/tg/<path:method>\", methods=[\"POST\"])")
    content = content[:idx] + webhook_route + "\n" + content[idx:]

run_hook = """
        global listen_mode
        offset = 0
        _poll_failures = 0
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "")
        import queue
        if not hasattr(self, "router_queue"):
            self.router_queue = queue.Queue()
            
        if webhook_base and MOON_ENV == "stable":
            wh_url = f"{webhook_base.rstrip('/')}/api/telegram/webhook/{self.token}"
            self.api_call("setWebhook", {"url": wh_url})
            add_web_log("DEBUG", f"Webhook configurado para {self.bot_username}: {wh_url}")

        while self.running:
            try:
                # Si es un Sub-Bot o tiene Webhook activado, lee de la cola
                if MOON_ENV != "stable" or webhook_base:
                    try:
                        update = self.router_queue.get(timeout=10)
                        res = {"ok": True, "result": [update]}
                    except queue.Empty:
                        self.run_periodic_maintenance()
                        continue
                else:
                    res = self.api_call("getUpdates", build_get_updates_payload(offset, allowed_updates=DEFAULT_ALLOWED_UPDATES))
"""
import re
pattern = re.compile(r'        global listen_mode\n        offset = 0\n        _poll_failures = 0\n        while self.running:\n            try:\n                res = self.api_call\("getUpdates", build_get_updates_payload\(offset, allowed_updates=DEFAULT_ALLOWED_UPDATES\)\)')

content = pattern.sub(run_hook.strip("\n"), content, count=1)

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
