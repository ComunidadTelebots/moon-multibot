# Usar imagen base ligera de Python
FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (incluyendo git para auto-update)
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto del Dashboard (Producción)
EXPOSE 5000

# Comando para ejecutar el bot (ahora usa el script de arranque para gestionar updates)
CMD ["bash", "start.sh"]
