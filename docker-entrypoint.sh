#!/bin/bash
set -e

echo "🔧 [$(date)] Starting AKS Cost Optimizer..."
echo "📁 Working directory: $(pwd)"
echo "👤 Running as: $(whoami)"
echo "🐍 Python version: $(python --version)"

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

# Start Flask application
echo "🚀 Starting Flask application..."
cd /app

# Use the simplest approach - direct python execution
# This ensures main.py's initialization runs properly
exec python app/main/main.py