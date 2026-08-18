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
            
            # Comprobación de seguridad por si el contenedor está reiniciando o faltan stats
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            if not cpu_stats or not precpu_stats:
                continue
                
            cpu_usage = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            precpu_usage = precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            
            system_cpu_usage = cpu_stats.get('system_cpu_usage', 0)
            presystem_cpu_usage = precpu_stats.get('system_cpu_usage', 0)
            
            # En algunas versiones de Docker/cgroups v2, system_cpu_usage puede no estar, intentamos sacarlo de online_cpus
            if not system_cpu_usage:
                system_cpu_usage = cpu_stats.get('online_cpus', 1) * 1000000000 # Dummy fallback
                presystem_cpu_usage = 0
                
            cpu_delta = cpu_usage - precpu_usage
            system_delta = system_cpu_usage - presystem_cpu_usage
            
            if system_delta > 0.0 and cpu_delta > 0.0:
                percpu_usage = cpu_stats.get('cpu_usage', {}).get('percpu_usage')
                num_cpus = len(percpu_usage) if percpu_usage else cpu_stats.get('online_cpus', 1)
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
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
