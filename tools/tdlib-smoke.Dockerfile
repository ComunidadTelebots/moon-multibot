FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl libssl3 zlib1g libc++1 libc++abi1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir python-dotenv requests
ARG TDLIB_SO_URL=https://github.com/ComunidadTelebots/moon-multibot/releases/download/tdlib-prebuilt/libtdjson.so
RUN curl -fL "$TDLIB_SO_URL" -o /usr/local/lib/libtdjson.so && ldconfig
WORKDIR /app
COPY core/config.py core/tdlib_client.py core/tdlib_receiver.py ./core/
COPY core/telegram_api.py core/traffic_control.py core/operations_telemetry.py core/bot_endpoint.py ./core/
COPY core/persistent_inbox.py ./core/
COPY plugins/calculator.py ./plugins/
COPY tools/tdlib_smoke.py ./
COPY tools/gateway_smoke.py ./
CMD ["python", "tdlib_smoke.py"]
