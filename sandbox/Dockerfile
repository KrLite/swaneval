FROM python:3.11-slim

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 -m appuser \
    && groupadd docker \
    && usermod -aG docker appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl docker.io && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "ms-enclave[docker]==0.0.4"

USER appuser

EXPOSE 8000

CMD ["ms-enclave", "server", "--host", "0.0.0.0", "--port", "8000"]
