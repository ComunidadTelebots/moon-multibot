with open('docker-compose.release.yml', 'rb') as f:
    content = f.read()
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]
with open('docker-compose.release.yml', 'wb') as f:
    f.write(content)
print("BOM removed.")
