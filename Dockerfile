# ── Etapa 1: compilar TDLib ──────────────────────────────────────
FROM ubuntu:22.04 AS tdlib-builder

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt-get update && apt-get install -y \
    tzdata \
    make git zlib1g-dev libssl-dev gperf php-cli cmake \
    clang-14 libc++-14-dev libc++abi-14-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth=1 https://github.com/tdlib/td.git /td

WORKDIR /td
RUN mkdir build && cd build && \
    CXXFLAGS="-stdlib=libc++" CC=/usr/bin/clang-14 CXX=/usr/bin/clang++-14 \
    cmake -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX:PATH=../example/python/tdlib .. && \
    cmake --build . --target install

# ── Etapa 2: imagen final ─────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc git curl libssl3 zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo el binario compilado de TDLib
COPY --from=tdlib-builder /td/example/python/tdlib/lib/libtdjson.so /usr/local/lib/
RUN ldconfig

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["bash", "start.sh"]
