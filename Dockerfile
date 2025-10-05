# AKS Cost Optimizer - PyInstaller Binary Protection
# Most secure approach - compiles to standalone executable
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install UPX (optional compression) - handle different architectures
RUN apt-get update && \
    (apt-get install -y --no-install-recommends upx-ucl || \
     apt-get install -y --no-install-recommends upx || \
     echo "UPX not available, skipping compression") && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install requirements
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyInstaller
RUN pip install --no-cache-dir pyinstaller

# Copy application code
COPY analytics/ ./analytics/
COPY application/ ./application/
COPY domain/ ./domain/
COPY infrastructure/ ./infrastructure/
COPY machine_learning/ ./machine_learning/
COPY presentation/ ./presentation/
COPY shared/ ./shared/
COPY config/ ./config/
COPY main.py production_main.py ./

# Create PyInstaller spec file for better control
RUN echo "# -*- mode: python ; coding: utf-8 -*-" > main.spec && \
    echo "block_cipher = None" >> main.spec && \
    echo "a = Analysis(['main.py']," >> main.spec && \
    echo "             pathex=['/build']," >> main.spec && \
    echo "             binaries=[]," >> main.spec && \
    echo "             datas=[('presentation/web/templates', 'presentation/web/templates'), ('presentation/web/static', 'presentation/web/static'), ('machine_learning/data', 'machine_learning/data'), ('config', 'config')]," >> main.spec && \
    echo "             hiddenimports=['flask', 'azure.identity', 'azure.mgmt.containerservice', 'azure.mgmt.monitor', 'azure.mgmt.resource', 'azure.mgmt.costmanagement', 'azure.mgmt.consumption', 'azure.mgmt.loganalytics', 'azure.monitor.query', 'azure.mgmt.core', 'azure.mgmt.compute', 'azure.mgmt.network', 'azure.mgmt.storage', 'azure.mgmt.authorization', 'kubernetes', 'sklearn.ensemble', 'pandas', 'pandas.core.api', 'pandas.core.groupby', 'pandas.core.groupby.generic', 'pandas.core.frame', 'pandas.core.generic', 'pandas.core.window', 'pandas.core.window.ewm', 'pandas._libs', 'pandas._libs.algos', 'pandas._libs.groupby', 'pandas._libs.reduction', 'pandas._libs.lib', 'pandas._libs.hashtable', 'pandas._libs.tslib', 'pandas._libs.index', 'numpy', 'sqlite3', 'jinja2', 'werkzeug', 'matplotlib.backends.backend_agg', 'seaborn', 'plotly', 'networkx', 'psutil', 'reportlab', 'xlsxwriter', 'aiohttp', 'requests', 'schedule', 'sqlalchemy', 'cryptography', 'prometheus_client', 'structlog', 'redis', 'gunicorn']," >> main.spec && \
    echo "             hookspath=[]," >> main.spec && \
    echo "             hooksconfig={}," >> main.spec && \
    echo "             runtime_hooks=[]," >> main.spec && \
    echo "             excludes=[]," >> main.spec && \
    echo "             win_no_prefer_redirects=False," >> main.spec && \
    echo "             win_private_assemblies=False," >> main.spec && \
    echo "             cipher=block_cipher," >> main.spec && \
    echo "             noarchive=False)" >> main.spec && \
    echo "pyz = PYZ(a.pure, a.zipped_data," >> main.spec && \
    echo "          cipher=block_cipher)" >> main.spec && \
    echo "exe = EXE(pyz," >> main.spec && \
    echo "          a.scripts," >> main.spec && \
    echo "          a.binaries," >> main.spec && \
    echo "          a.zipfiles," >> main.spec && \
    echo "          a.datas," >> main.spec && \
    echo "          []," >> main.spec && \
    echo "          name='aks-cost-optimizer'," >> main.spec && \
    echo "          debug=False," >> main.spec && \
    echo "          bootloader_ignore_signals=False," >> main.spec && \
    echo "          strip=False," >> main.spec && \
    echo "          upx=False," >> main.spec && \
    echo "          upx_exclude=[]," >> main.spec && \
    echo "          console=True," >> main.spec && \
    echo "          disable_windowed_traceback=False," >> main.spec && \
    echo "          target_arch=None," >> main.spec && \
    echo "          codesign_identity=None," >> main.spec && \
    echo "          entitlements_file=None)" >> main.spec

# Build the binary
RUN pyinstaller --clean main.spec

# Final production stage - use same base as builder for GLIBC compatibility
FROM python:3.11-slim-bookworm

# Install runtime dependencies and Azure CLI
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    jq \
    # Runtime libraries for ML and graphics (required by your dependencies)
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgcc-s1 \
    libfontconfig1 \
    libxft2 \
    # Additional runtime libraries
    libssl3 \
    libffi8 \
    && curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user
RUN groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser -s /bin/bash -m appuser

# Create application directories
WORKDIR /app
RUN mkdir -p \
    /app/infrastructure/persistence/database \
    /app/machine_learning/data \
    /app/logs \
    /home/appuser/.azure \
    && chown -R appuser:appuser /app /home/appuser

# Copy the compiled binary (no source code!)
COPY --from=builder /build/dist/aks-cost-optimizer /app/
COPY --chown=appuser:appuser deploy/docker/docker-entrypoint-binary.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /app/aks-cost-optimizer

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    MPLBACKEND="Agg" \
    AZURE_CONFIG_DIR="/home/appuser/.azure" \
    AZURE_CORE_COLLECT_TELEMETRY=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# Use entrypoint script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["./aks-cost-optimizer"]