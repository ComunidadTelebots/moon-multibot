import re

with open("moon_multibot.py", "r", encoding="utf-8") as f:
    bot = f.read()

old_log = """def add_web_log(lvl, txt):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    web_logs.append({"time": t, "level": lvl, "text": txt})
    if len(web_logs) > 50: web_logs.pop(0)
    with open("data/bot.log", "a", encoding="utf-8") as f:
        f.write(f"[{t}] [{lvl}] {txt}\\n")"""

new_log = """def add_web_log(lvl, txt):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    web_logs.append({"time": t, "level": lvl, "text": txt})
    if len(web_logs) > 50: web_logs.pop(0)
    
    log_path = "data/bot.log"
    try:
        if os.path.exists(log_path) and os.path.getsize(log_path) > 5 * 1024 * 1024:
            if os.path.exists(log_path + ".1"):
                os.remove(log_path + ".1")
            os.rename(log_path, log_path + ".1")
    except Exception:
        pass

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{t}] [{lvl}] {txt}\\n")"""

if old_log in bot:
    bot = bot.replace(old_log, new_log)
    with open("moon_multibot.py", "w", encoding="utf-8") as f:
        f.write(bot)
    print("Log rotation implemented successfully.")
else:
    print("Could not find the target code to patch.")
