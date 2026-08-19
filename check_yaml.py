with open('docker-compose.release.yml', 'rb') as f:
    content = f.read()

bad_chars = []
for i, b in enumerate(content):
    if b < 32 and b not in (9, 10, 13):
        bad_chars.append((i, b))

print("Bad chars found:", bad_chars)
print("Contains tabs?", b'\t' in content)
