with open("autoscaler/autoscaler.py", "r", encoding="utf-8") as f:
    content = f.read()

# Make the CPU stat parsing safer
safe_parsing = """
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
"""

import re
# Regex to match the old stats reading block
pattern = re.compile(r'            stats = container\.stats\(stream=False\).*?                total_cpu \+= cpu_percent', re.DOTALL)
content = pattern.sub(safe_parsing.strip("\n"), content)

with open("autoscaler/autoscaler.py", "w", encoding="utf-8") as f:
    f.write(content)
