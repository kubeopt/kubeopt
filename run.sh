#!/bin/bash
# Quick fix script for Azure CLI read-only filesystem issue

set -e

echo "🔧 Fixing Azure CLI authentication issue..."

# Step 4: Rebuild and restart
echo "🔄 Rebuilding Docker image..."
docker-compose down
docker-compose build --no-cache

echo "🚀 Starting container..."
docker-compose up -d

# Step 5: Wait and test
echo "⏳ Waiting for service to start..."
sleep 10
