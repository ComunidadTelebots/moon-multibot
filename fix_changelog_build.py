import os

with open("CHANGELOG.md", "r", encoding="utf-8") as f:
    content = f.read()

# Reemplazar la seccion anterior que no tenia el cuarto numero
import re
content = re.sub(
    r"## \[v18\.25\.15-alpha\]", 
    "## [v18.25.15.17-alpha]", 
    content, 
    flags=re.DOTALL
)

with open("CHANGELOG.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

