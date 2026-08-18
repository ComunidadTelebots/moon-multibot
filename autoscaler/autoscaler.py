import docker
import time
import os

MIN_REPLICAS = int(os.getenv("MIN_REPLICAS", "2"))
MAX_REPLICAS = int(os.getenv("MAX_REPLICAS", "5"))
CPU_UP = float(os.getenv("CPU_THRESHOLD_UP", "70.0"))
CPU_DOWN = float(os.getenv("CPU_THRESHOLD_DOWN", "20.0"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

# Lista de servicios que pueden autoescalar
TARGET_SERVICES = [
    "moonbot",          # Estable
    "moonbot-rc",       # Release Candidate
    "moonbot-beta",     # Beta
    "moonbot-alfa",     # Alfa
    "moonbot-prealfa"   # Pre-Alfa
]

client = docker.from_env()

def get_service_cpu_usage(service_name):
    try:
        containers = [c for c in client.containers.list() if c.labels.get('com.docker.compose.service') == service_name]
        if not containers:
            return 0.0, 0
        
        total_cpu = 0.0
        for container in containers:
            stats = container.stats(stream=False)
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0.0 and cpu_delta > 0.0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1])) * 100.0
                total_cpu += cpu_percent
                
        avg_cpu = total_cpu / len(containers)
        return avg_cpu, len(containers)
    except Exception as e:
        print(f"Error reading CPU for {service_name}: {e}")
        return 0.0, 0

def scale_service(service_name, target_replicas):
    print(f"Autoescalando {service_name} a {target_replicas} réplicas...")
    # Usamos os.system porque docker-py no soporta bien scale de docker-compose
    cmd = f"docker-compose -f /app/compose/docker-compose.yml -f /app/compose/docker-compose.release.yml up -d --scale {service_name}={target_replicas} --no-recreate"
    os.system(cmd)

print("Iniciando MoonBot AutoScaler Multientorno...", flush=True)

while True:
    for service in TARGET_SERVICES:
        cpu, replicas = get_service_cpu_usage(service)
        if replicas == 0:
            continue
            
        print(f"[{service}] CPU: {cpu:.1f}% | Réplicas: {replicas}")
        
        if cpu > CPU_UP and replicas < MAX_REPLICAS:
            print(f"[{service}] ALERTA DE CARGA: {cpu:.1f}% supera umbral de {CPU_UP}%. Escalando ARRIBA.")
            scale_service(service, replicas + 1)
            time.sleep(10) # Esperar a que arranque
            
        elif cpu < CPU_DOWN and replicas > MIN_REPLICAS:
            print(f"[{service}] BAJA CARGA: {cpu:.1f}% bajo umbral de {CPU_DOWN}%. Escalando ABAJO.")
            scale_service(service, replicas - 1)
            time.sleep(10)
            
    time.sleep(CHECK_INTERVAL)
