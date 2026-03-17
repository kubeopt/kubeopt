# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python dependencies
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /install

COPY requirements/requirements.txt .

RUN pip install --no-cache-dir --target=/install \
    --prefer-binary \
    --no-warn-script-location \
    -r requirements.txt

RUN find /install -type f -name "*.pyc" -delete && \
    find /install -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "test" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "*.c" -delete 2>/dev/null || true && \
    find /install -name "*.pyx" -delete 2>/dev/null || true && \
    find /install -name "*.so" -exec strip {} \; 2>/dev/null || true

# Stage 3: Production
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /install /usr/local/lib/python3.11/site-packages

WORKDIR /app

# Copy application code
COPY *.py ./
COPY analytics/ ./analytics/
COPY application/ ./application/
COPY infrastructure/ ./infrastructure/
COPY machine_learning/ ./machine_learning/
COPY presentation/ ./presentation/
COPY shared/ ./shared/
COPY config/ ./config/
COPY algorithms/ ./algorithms/
COPY requirements/ ./requirements/

# Copy built frontend from Stage 1
COPY --from=frontend /frontend/dist/ ./frontend/dist/

# Create necessary directories
RUN mkdir -p \
    /app/logs \
    /app/config \
    /app/machine_learning/data \
    /root/.azure

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    AZURE_CONFIG_DIR=/root/.azure

EXPOSE 5010

CMD ["python", "main.py"]
