with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to add the forwarding logic into patched_api_call for the stable bot
forward_logic = """
            # En Stable, comportamiento normal, pero procesando reenvíos a sub-bots
            res = original_api_call(method, payload, files, timeout, silent)
            if MOON_ENV == "stable" and method == "getUpdates" and res.get("ok"):
                for item in res.get("result", []):
                    msg = item.get("message") or item.get("callback_query", {}).get("message")
                    if msg:
                        uid = msg.get("from", {}).get("id")
                        try:
                            from core.db import get_db
                            with get_db() as db_con:
                                row = db_con.execute("SELECT release_channels FROM users WHERE uid = ?", (uid,)).fetchone()
                                if row and row[0]:
                                    channels = [c.strip().lower() for c in row[0].split(",")]
                                    for target in ["alfa", "beta", "rc", "prealfa"]:
                                        if target in channels:
                                            try:
                                                requests.post(f"http://moonbot-{target}:5000/api/internal_update", json={"bot_token": bot.token, "update": item}, timeout=2)
                                            except: pass
                        except: pass
            return res
"""

import re
pattern = re.compile(r'            # En Stable, comportamiento normal\n            return original_api_call\(method, payload, files, timeout, silent\)')
content = pattern.sub(forward_logic.strip("\n"), content)

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
