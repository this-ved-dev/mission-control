# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.24 AS uv

FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# Dependencies only, so code edits don't invalidate this layer.
FROM base AS build
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# `docker compose run --rm test`: the full suite, offline, on the fake model.
FROM build AS test
RUN uv sync --locked --no-install-project
COPY openapi.json ./
COPY app ./app
COPY tests ./tests
ENV MC_LLM=fake
CMD ["uv", "run", "--no-sync", "pytest"]

FROM base AS runtime
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/data \
    && chown app /app/data
COPY --from=build /app/.venv /app/.venv
COPY app ./app
ENV PATH="/app/.venv/bin:$PATH" \
    MC_DB_PATH=/app/data/mission_control.db
USER app
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
