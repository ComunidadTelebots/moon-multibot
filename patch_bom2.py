with open("moon_multibot.py", "rb") as f:
    raw = f.read()

# Remove UTF-8 BOM if present anywhere
raw = raw.replace(b'\xef\xbb\xbf', b'')
# Remove UTF-16 BOMs just in case
raw = raw.replace(b'\xff\xfe', b'')
raw = raw.replace(b'\xfe\xff', b'')

with open("moon_multibot.py", "wb") as f:
    f.write(raw)
