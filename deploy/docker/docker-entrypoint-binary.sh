#!/bin/bash
set -e

echo "🔧 [$(date)] Starting AKS Cost Optimizer (Binary Mode)..."
echo "📁 Working directory: $(pwd)"
echo "👤 Running as: $(whoami)"
echo "🔒 Binary version: Secure (no source code)"
echo "🐍 Python runtime: $(python --version 2>/dev/null || echo 'Not needed for binary')"

# Setup Azure credentials
echo "🔑 Setting up Azure credentials..."
mkdir -p /home/appuser/.azure

if [ -d "/tmp/host-azure" ]; then
    echo "📋 Copying Azure credentials from host..."
    for file in azureProfile.json accessTokens.json clouds.config config msal_token_cache.json; do
        if [ -f "/tmp/host-azure/$file" ]; then
            cp "/tmp/host-azure/$file" "/home/appuser/.azure/" 2>/dev/null || true
            echo "  ✅ Copied $file"
        fi
    done
    chmod -R 700 /home/appuser/.azure
fi

# Verify Azure CLI is available
if command -v az >/dev/null 2>&1; then
    echo "✅ Azure CLI available: $(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo 'installed')"
else
    echo "⚠️  Azure CLI not found"
fi

# Start the compiled binary
echo "🚀 Starting AKS Cost Optimizer binary..."
cd /app

# Check if binary exists and is executable
if [ -x "./aks-cost-optimizer" ]; then
    echo "✅ Binary found and executable"
    exec "$@"
else
    echo "❌ Binary not found or not executable"
    ls -la /app/
    exit 1
fi