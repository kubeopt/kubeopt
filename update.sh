#!/bin/bash
# Update AKS Cost Optimizer while preserving data

echo "🔄 Updating AKS Cost Optimizer..."

# Stop current container (but keep volumes)
docker-compose down

# Build new image
docker-compose build --no-cache

# Start with preserved data
docker-compose up -d

echo "✅ Update complete! Data preserved in volumes."
echo "🌐 Access at: http://localhost:5020"
