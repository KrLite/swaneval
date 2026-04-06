FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl docker.io && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "ms-enclave[docker]"

EXPOSE 8000

CMD ["ms-enclave", "server", "--host", "0.0.0.0", "--port", "8000"]
