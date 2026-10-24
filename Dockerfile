FROM python:3.10-slim

WORKDIR /app

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

# Conserva índices y paquetes descargados entre reconstrucciones con BuildKit.
RUN --mount=type=cache,id=moonbot-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=moonbot-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc git curl libssl3 zlib1g tesseract-ocr tesseract-ocr-spa nodejs npm \
    && test -x /usr/bin/curl && test -x /usr/bin/tesseract \
    && npm install -g @tgcloud/cli@0.2.0

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# @tgcloud/cli 0.2.0 no filtra los tombstones booleanos al guardar snapshots.
RUN node cintiaandrea_bot/scripts/patch-tgcloud-cli.mjs "$(npm root -g)/@tgcloud/cli/src/core/snapshot.js"

# Usar modo no bufferizado para logs inmediatos
ENV PYTHONUNBUFFERED=1

CMD ["python", "moon_multibot.py"]
