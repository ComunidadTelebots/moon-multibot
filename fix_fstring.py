with open("clean_merge.py", "r", encoding="utf-8") as f:
    script = f.read()

script = script.replace('`<base href="${origin}/">`', '`<base href="${origin}/">`.replace("${origin}", origin)')
with open("clean_merge.py", "w", encoding="utf-8") as f:
    f.write(script)
