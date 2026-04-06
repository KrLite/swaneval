FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

RUN pip install --no-cache-dir "evalscope[service]==1.5.1"

COPY custom_metrics/ /app/custom_metrics/
COPY startup.py /app/startup.py

WORKDIR /app
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 9000

CMD ["python", "startup.py"]
