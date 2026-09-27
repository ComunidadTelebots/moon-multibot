FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates cmake clang gperf make libssl-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*
ARG BOT_API_COMMIT=e3e9dd8e5b3d7ab8537cd5a10dc31d5ffa8f82d1
RUN git clone https://github.com/tdlib/telegram-bot-api.git /src && cd /src && git checkout "$BOT_API_COMMIT" && git submodule update --init --recursive
RUN cmake -S /src -B /build -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ && cmake --build /build --target telegram-bot-api -j2

FROM python:3.14-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libssl3 zlib1g libstdc++6 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir python-dotenv && groupadd -r telegram && useradd -r -g telegram telegram && mkdir -p /var/lib/telegram-bot-api && chown telegram:telegram /var/lib/telegram-bot-api
COPY --from=build /build/telegram-bot-api /usr/local/bin/telegram-bot-api
COPY --from=build /src/LICENSE_1_0.txt /licenses/telegram-bot-api.txt
COPY deploy/telegram-gateway/entrypoint.py /app/entrypoint.py
USER telegram
WORKDIR /var/lib/telegram-bot-api
EXPOSE 8081
ENTRYPOINT ["python", "/app/entrypoint.py"]
