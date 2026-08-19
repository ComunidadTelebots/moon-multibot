with open("docker-compose.yml", "r", encoding="utf-8") as f:
    content = f.read()

# We need to remove the deploy replicas from moon_ollama
lines = content.split("\n")
new_lines = []
skip = False
in_ollama = False

for line in lines:
    if line.strip() == "moon_ollama:":
        in_ollama = True
    
    if in_ollama and line.strip() == "deploy:":
        skip = True
        continue
        
    if skip:
        if line.startswith("    ") and not line.startswith("      "):
            # back to same level as deploy
            skip = False
        else:
            continue
            
    new_lines.append(line)

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))
