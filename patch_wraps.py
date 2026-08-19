with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

if "from functools import wraps" not in content:
    content = "from functools import wraps\n" + content

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
