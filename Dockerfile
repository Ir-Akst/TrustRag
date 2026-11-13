# Multi-stage secure Dockerfile for TrustRAG API & Runtime
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed wheels and python environment
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source, configs, and assets
COPY src/ /app/src/
COPY configs/ /app/configs/
COPY pyproject.toml /app/pyproject.toml

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV TRUSTRAG_HOST=0.0.0.0
ENV TRUSTRAG_PORT=3000

# Create non-root user for security
RUN useradd -m -u 1001 trustrag && \
    mkdir -p /app/data /app/logs && \
    chown -R trustrag:trustrag /app

USER trustrag

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["python", "-m", "trustrag.api.server", "--host", "0.0.0.0", "--port", "3000"]

