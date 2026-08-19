with open("docker-compose.release.yml", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("    container_name: moonbot-rc\n", "")
content = content.replace("    container_name: moonbot-beta\n", "")
content = content.replace("    container_name: moonbot-alfa\n", "")
content = content.replace("    container_name: moonbot-prealfa\n", "")

with open("docker-compose.release.yml", "w", encoding="utf-8") as f:
    f.write(content)
