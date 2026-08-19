FROM python:3.10-slim

WORKDIR /app

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

# Conserva índices y paquetes descargados entre reconstrucciones con BuildKit.
RUN --mount=type=cache,id=moonbot-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=moonbot-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc git curl libssl3 zlib1g tesseract-ocr tesseract-ocr-spa \
    && test -x /usr/bin/curl && test -x /usr/bin/tesseract

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Usar modo no bufferizado para logs inmediatos
ENV PYTHONUNBUFFERED=1

CMD ["python", "moon_multibot.py"]
