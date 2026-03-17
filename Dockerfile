# Optimized Debian slim build with aggressive cleanup
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create install directory
RUN mkdir -p /install

# Copy requirements and install to specific location
COPY requirements/requirements.txt .

# Install packages to isolated location with pre-built wheels preference
RUN pip install --no-cache-dir --target=/install \
    --prefer-binary \
    --no-warn-script-location \
    -r requirements.txt

# Aggressive cleanup to reduce size
RUN find /install -type f -name "*.pyc" -delete && \
    find /install -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "test" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /install -name "*.c" -delete 2>/dev/null || true && \
    find /install -name "*.pyx" -delete 2>/dev/null || true && \
    find /install -name "*.so" -exec strip {} \; 2>/dev/null || true

# Production stage - minimal Debian slim
FROM python:3.11-slim

# Install only essential runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /install /usr/local/lib/python3.11/site-packages

# Set working directory
WORKDIR /app

# Copy application code (as root for Railway volume access)
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
COPY frontend/dist/ ./frontend/dist/

# Create necessary directories
RUN mkdir -p \
    /app/logs \
    /app/config \
    /app/machine_learning/data \
    /root/.azure

# Run as root for Railway volume access
# Railway volumes are owned by root, so we need root access
# Note: Set RAILWAY_RUN_UID=0 in Railway if needed

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    AZURE_CONFIG_DIR=/root/.azure

# Expose port
EXPOSE 5010

# No health check needed - app runs fine

# Start application
CMD ["python", "main.py"]