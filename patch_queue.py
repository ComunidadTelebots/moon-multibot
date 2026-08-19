with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('if not hasattr(bot, "router_queue"):', 'import queue\n        if not hasattr(bot, "router_queue"):')

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
