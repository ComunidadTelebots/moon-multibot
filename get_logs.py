import time

def monitor_logs():
    import docker
    client = docker.from_env()
    try:
        container = client.containers.get("moonbot-moonbot-1")
        logs = container.logs(tail=50).decode("utf-8")
        print("=== MOONBOT LOGS ===")
        print(logs)
    except Exception as e:
        print(f"Error: {e}")

monitor_logs()
