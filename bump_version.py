import codecs
import re

# Update CHANGELOG.md
with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    changelog = f.read()

changelog = changelog.replace("## [v18.26.0-alpha]", "## [v18.26.15.16-alpha]")

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(changelog)

# Update core/config.py
with codecs.open("core/config.py", "r", "utf-8") as f:
    config = f.read()

config = re.sub(r'APP_VERSION\s*=\s*".*?"', 'APP_VERSION = "v18.26.15.16-alpha"', config)

with codecs.open("core/config.py", "w", "utf-8") as f:
    f.write(config)

print("Version updated")
