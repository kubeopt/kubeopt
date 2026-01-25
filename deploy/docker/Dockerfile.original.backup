# AKS Cost Optimizer - Clean Architecture Docker Image
# Multi-stage build for minimal production image
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install requirements
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final production stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies and Azure CLI
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    # Runtime libraries for ML and graphics
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgcc-s1 \
    # Azure CLI dependencies
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    # Utility tools
    jq \
    && curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user with bash shell (required for Azure CLI)
RUN groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser -s /bin/bash -m appuser

# Create application directories with proper permissions
WORKDIR /app
RUN mkdir -p \
    /app/infrastructure/persistence/database \
    /app/machine_learning/data \
    /app/logs \
    /app/shared/cache \
    /home/appuser/.azure \
    && chown -R appuser:appuser /app /home/appuser

# Copy entrypoint script and make executable
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy clean architecture application code
COPY --chown=appuser:appuser analytics/ ./analytics/
COPY --chown=appuser:appuser application/ ./application/
COPY --chown=appuser:appuser domain/ ./domain/
COPY --chown=appuser:appuser infrastructure/ ./infrastructure/
COPY --chown=appuser:appuser machine_learning/ ./machine_learning/
COPY --chown=appuser:appuser presentation/ ./presentation/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser main.py production_main.py requirements*.txt ./

# Create __init__.py files for Python modules
RUN find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /app -type d -exec touch {}/__init__.py \; 2>/dev/null || true \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables for clean architecture
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    FLASK_APP="main:app" \
    FLASK_ENV="production" \
    MPLBACKEND="Agg" \
    AZURE_CONFIG_DIR="/home/appuser/.azure" \
    AZURE_CORE_COLLECT_TELEMETRY=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# Use entrypoint script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "main.py"]