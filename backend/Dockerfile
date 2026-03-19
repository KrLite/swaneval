# ── Stage 1: Build dependencies ──
FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# ── Stage 2: Production runner ──
FROM python:3.12-slim AS runner

WORKDIR /app

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app /app

RUN mkdir -p /data && chown appuser:appgroup /data

USER appuser
EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
