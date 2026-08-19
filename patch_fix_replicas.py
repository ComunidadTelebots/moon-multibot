with open("docker-compose.yml", "r", encoding="utf-8") as f:
    content = f.read()

import re
# Remove deploy replicas block from moonbot
content = re.sub(r'    deploy:\n      replicas: 2\n      restart_policy:\n        condition: any\n', '', content)

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(content)

with open("autoscaler/autoscaler.py", "r", encoding="utf-8") as f:
    auto_content = f.read()

# Remove moonbot from TARGET_SERVICES
auto_content = auto_content.replace('    "moonbot",          # Estable\n', '')

with open("autoscaler/autoscaler.py", "w", encoding="utf-8") as f:
    f.write(auto_content)
