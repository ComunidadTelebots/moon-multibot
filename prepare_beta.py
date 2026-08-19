import os
import codecs

count = 0
for root_dir, dirs, files in os.walk("."):
    if ".git" in root_dir or "node_modules" in root_dir: continue
    for file in files:
        if file.endswith("manifest.py"):
            path = os.path.join(root_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if '"release_channel": "alpha"' in content:
                content = content.replace('"release_channel": "alpha"', '"release_channel": "beta"')
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1
print(f"Updated {count} manifests for beta.")

# Update CHANGELOG
with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

changelog = changelog.replace("v18.26.15.16-alpha", "v18.26.15.16-beta")
# We also update the top line to indicate this is the Beta Release
changelog = changelog.replace("## [v18.26.15.16-beta] - 2026-08-19 (Fusi\u00f3n Arquitect\u00f3nica de Interfaces)", 
                              "## [v18.26.15.16-beta] - 2026-08-19 (Release Beta Multi-Canal)")

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(changelog)
print("Changelog updated for beta.")
