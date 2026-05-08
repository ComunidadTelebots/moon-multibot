FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc git curl libssl3 zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Descarga libtdjson.so pre-compilado desde el Release de GitHub.
# Para actualizar TDLib: lanza el workflow "Compile & publish libtdjson.so"
# en GitHub Actions y luego reconstruye esta imagen.
ARG TDLIB_SO_URL=https://github.com/ComunidadTelebots/moon-multibot/releases/download/tdlib-prebuilt/libtdjson.so
RUN curl -fL "${TDLIB_SO_URL}" -o /usr/local/lib/libtdjson.so \
    && ldconfig

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["bash", "start.sh"]
