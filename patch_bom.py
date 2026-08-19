with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Strip out any Byte Order Marks that got pushed to the middle of the file
content = content.replace("\ufeff", "")

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
