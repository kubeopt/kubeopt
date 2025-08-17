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

echo "🔍 Testing Azure CLI in container..."
docker-compose exec -T aks-cost-optimizer az account show --query "{Name:name, ID:id}" -o table

if [ $? -eq 0 ]; then
    echo "✅ SUCCESS! Azure CLI is working in the container!"
    echo ""
    echo "Your app is now running at: http://localhost:5020"
    echo ""
    echo "Test multi-subscription access:"
    echo "  docker-compose exec aks-cost-optimizer az account list --output table"
else
    echo "⚠️  Azure CLI test failed. Checking logs..."
    docker-compose logs --tail=50
fi