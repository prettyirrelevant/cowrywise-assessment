FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

RUN apt update && apt install -y make

COPY uv.lock pyproject.toml Makefile /app/

COPY packages /app/packages

RUN uv sync --frozen --no-install-project --no-install-workspace --package=bookworm

RUN uv sync --locked --package=bookworm

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
