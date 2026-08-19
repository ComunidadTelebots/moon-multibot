import os
import re

count = 0
for root_dir, dirs, files in os.walk("."):
    # Skip .git and plugins etc
    if ".git" in root_dir or "node_modules" in root_dir:
        continue
    for file in files:
        if file.endswith("manifest.py"):
            path = os.path.join(root_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            # Strategy 1: FEATURES.append({"id": ...
            content = re.sub(r'FEATURES\.append\(\s*\{\s*"id"', 'FEATURES.append({"release_channel": "alpha", "id"', content)
            
            # Strategy 2: {"id": ...} inside a list FEATURES = [ ... ]
            content = re.sub(r'\{\s*"id":', '{"release_channel": "alpha", "id":', content)

            if content != original:
                # Deduplicate if we accidentally added it twice
                content = content.replace('"release_channel": "alpha", "release_channel": "alpha",', '"release_channel": "alpha",')
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1

print(f"Updated {count} manifest files with alpha release_channel.")
