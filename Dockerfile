# Use Python 3.11 for compatibility
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

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install requirements
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies and Azure CLI with security updates
RUN apt-get update && \
    # IMPORTANT: Upgrade all packages to patch vulnerabilities
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    # Runtime libraries
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgcc-s1 \
    # Required for Azure CLI
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    # Additional tools
    jq \
    && curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user with bash shell (needed for az cli)
RUN groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser -s /bin/bash -m appuser

# Create app directories with correct permissions
WORKDIR /app
RUN mkdir -p /app/data /app/logs /app/cache /app/models /app/reports \
    && mkdir -p /home/appuser/.azure \
    && chown -R appuser:appuser /app /home/appuser

# Copy entrypoint script
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser requirements*.txt ./

# Create __init__.py files if needed
RUN find /app/app -type d -exec touch {}/__init__.py \; 2>/dev/null || true \
    && chown -R appuser:appuser /app/app

# Switch to non-root user
USER appuser

# Environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    FLASK_APP="app.main.main:app" \
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
CMD ["python", "-m", "app.main.main"]