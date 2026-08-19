with open('docker-compose.release.yml', 'rb') as f:
    content = bytearray(f.read())

clean_content = bytearray()
for b in content:
    if b >= 32 or b in (10, 13):
        clean_content.append(b)

with open('docker-compose.release.yml', 'wb') as f:
    f.write(clean_content)
