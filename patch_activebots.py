with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace active_bots.values() with active_bots
content = content.replace("active_bots.values()", "active_bots")

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
