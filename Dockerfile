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

# Create non-root user (Debian version)
RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -s /bin/bash -m appuser

# Set working directory
WORKDIR /app

# Copy application code (only Python files, not build artifacts)
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser analytics/ ./analytics/
COPY --chown=appuser:appuser application/ ./application/
COPY --chown=appuser:appuser infrastructure/ ./infrastructure/
COPY --chown=appuser:appuser machine_learning/ ./machine_learning/
COPY --chown=appuser:appuser presentation/ ./presentation/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser algorithms/ ./algorithms/
COPY --chown=appuser:appuser requirements/ ./requirements/

# Create necessary directories with correct permissions
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/config \
    /app/machine_learning/data \
    /home/appuser/.azure \
    && chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    DATABASE_PATH=/app/data/aks_optimizer.db \
    AZURE_CONFIG_DIR=/home/appuser/.azure

# Expose port
EXPOSE 5010

# No health check needed - app runs fine

# Start application
CMD ["python", "main.py"]