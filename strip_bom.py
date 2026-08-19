import os

directory = "core"
count = 0
for filename in os.listdir(directory):
    if filename.endswith(".py"):
        filepath = os.path.join(directory, filename)
        with open(filepath, "rb") as f:
            raw = f.read()
        if raw.startswith(b'\xef\xbb\xbf'):
            with open(filepath, "wb") as f:
                f.write(raw[3:])
            count += 1
            print(f"Removed BOM from {filename}")

if count == 0:
    print("No other files with BOM found.")
