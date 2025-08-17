#!/bin/bash
set -e

echo "🔧 Initializing Azure credentials..."

# Create .azure directory if it doesn't exist
mkdir -p /home/appuser/.azure

# Check if host Azure credentials are mounted
if [ -d "/tmp/host-azure" ]; then
    echo "📋 Copying Azure credentials from host..."
    
    # Copy essential credential files
    for file in azureProfile.json accessTokens.json clouds.config config msal_token_cache.json; do
        if [ -f "/tmp/host-azure/$file" ]; then
            cp "/tmp/host-azure/$file" "/home/appuser/.azure/"
            echo "  ✅ Copied $file"
        fi
    done
    
    # Set proper permissions
    chmod -R 700 /home/appuser/.azure
    
    echo "✅ Azure credentials initialized"
else
    echo "⚠️  No host Azure credentials found"
fi

# Test Azure CLI access
echo "🔍 Testing Azure CLI access..."
if az account show &>/dev/null; then
    echo "✅ Azure CLI authenticated successfully"
    az account show --query "{Name:name, ID:id}" -o table
else
    echo "⚠️  Azure CLI not authenticated"
fi

echo "🚀 Starting AKS Cost Optimizer..."
# Execute the main application
exec "$@"
