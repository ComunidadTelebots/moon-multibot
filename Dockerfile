# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

WORKDIR /app

# Conserva índices y paquetes descargados entre reconstrucciones con BuildKit.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc git curl libssl3 zlib1g tesseract-ocr tesseract-ocr-spa \
    && apt-get clean

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .

# Usa libtdjson.so local si fue copiado al contexto de build (setup_tdlib.sh),
# de lo contrario descarga el binario pre-compilado desde el GitHub Release.
ARG TDLIB_SO_URL=https://github.com/ComunidadTelebots/moon-multibot/releases/download/tdlib-prebuilt/libtdjson.so
RUN if [ -f libtdjson.so ]; then \
        echo "[TDLib] Usando binario local"; \
        mv libtdjson.so /usr/local/lib/libtdjson.so; \
    else \
        echo "[TDLib] Descargando desde GitHub Release"; \
        curl -fL "${TDLIB_SO_URL}" -o /usr/local/lib/libtdjson.so; \
    fi && ldconfig

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["bash", "start.sh"]
