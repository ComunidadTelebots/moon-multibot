import os
import codecs

# 1. Update feature_access.py
path_fa = "core/feature_access.py"
with codecs.open(path_fa, "r", "utf-8") as f:
    fa_content = f.read()

fa_content = fa_content.replace('RELEASE_CHANNELS = ("stable", "rc", "beta", "alpha")', 
                                'RELEASE_CHANNELS = ("stable", "rc", "beta", "alpha", "prealfa")')

with codecs.open(path_fa, "w", "utf-8") as f:
    f.write(fa_content)
print("Updated feature_access.py")

# 2. Retag 103 manifests
count = 0
for root_dir, dirs, files in os.walk("."):
    if ".git" in root_dir or "node_modules" in root_dir or "prealfa-src" in root_dir: continue
    for file in files:
        if file.endswith("manifest.py"):
            path = os.path.join(root_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if '"release_channel": "alpha"' in content:
                content = content.replace('"release_channel": "alpha"', '"release_channel": "prealfa"')
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1
print(f"Updated {count} manifests for prealfa.")

# 3. Update CHANGELOG
with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

changelog = changelog.replace("v18.26.15.16-alpha", "v18.26.15.16-prealfa")
changelog = changelog.replace("## [v18.26.15.16-prealfa] - 2026-08-19 (Fusi\u00f3n Arquitect\u00f3nica de Interfaces)", 
                              "## [v18.26.15.16-prealfa] - 2026-08-19 (Release Pre-Alfa Multi-Canal)")

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(changelog)
print("Changelog updated for prealfa.")
