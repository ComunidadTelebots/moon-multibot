with open("docker-compose.yml", "r", encoding="utf-8") as f:
    content = f.read()

deploy_block = """    deploy:
      replicas: 2
      restart_policy:
        condition: any
"""

if "replicas: 2" not in content:
    content = content.replace("    restart: unless-stopped\n", "    restart: unless-stopped\n" + deploy_block)

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(content)
