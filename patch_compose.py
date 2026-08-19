with open("docker-compose.yml", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("    container_name: moonbot\n", "")

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(content)
