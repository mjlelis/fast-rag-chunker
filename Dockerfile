# Dockerfile para fast-rag-chunker
# Ambiente isolado com Clang, LLVM, Rust e Python 3.12

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    clang \
    llvm \
    libclang-dev \
    valgrind \
    curl \
    git \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Instalação do Rust estável e nightly (com Miri)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable \
    && rustup toolchain install nightly \
    && rustup component add miri --toolchain nightly \
    && rustup component add clippy rustfmt

# Instalação do Maturin para builds Python/PyO3
RUN pip3 install --no-cache-dir --break-system-packages maturin pytest

WORKDIR /workspace
COPY . /workspace

CMD ["cargo", "test"]
