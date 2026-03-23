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

# Install kubectl and helm for K8s cluster management
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
      -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl && \
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app /app

RUN mkdir -p /data && chown appuser:appgroup /data

USER appuser
EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
