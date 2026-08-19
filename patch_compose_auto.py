with open("docker-compose.yml", "r", encoding="utf-8") as f:
    content = f.read()

autoscaler_block = """  autoscaler:
    build: ./autoscaler
    container_name: moonbot_autoscaler
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - .:/app/compose:ro
    environment:
      - MIN_REPLICAS=2
      - MAX_REPLICAS=5
      - CPU_THRESHOLD_UP=70
      - CPU_THRESHOLD_DOWN=20
      - CHECK_INTERVAL=30
"""

if "moonbot_autoscaler" not in content:
    content = content.replace("services:\n", "services:\n" + autoscaler_block)

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(content)
