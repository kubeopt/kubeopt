#!/bin/bash

echo "Docker build started"
docker build . -t kubeopt:latest 

echo "Docker build finished"
# Script to restart kubeopt container
echo "🔄 Restarting kubeopt container..."

# Stop and remove existing kubeopt containers
echo "🛑 Stopping existing kubeopt containers..."
docker stop kubeopt 2>/dev/null || echo "No running container named 'kubeopt' found"
docker rm kubeopt 2>/dev/null || echo "No container named 'kubeopt' to remove"

# Also clean up any containers from kubeopt:latest image
docker stop $(docker ps -q --filter "ancestor=kubeopt:latest") 2>/dev/null || true
docker rm $(docker ps -aq --filter "ancestor=kubeopt:latest") 2>/dev/null || true

# Run new container
echo "🚀 Starting new kubeopt container..."
docker run -d \
  --name kubeopt \
  -p 5030:5001 \
  --env-file .env \
  kubeopt:latest

echo "✅ Container started successfully!"
echo "🌐 Access the app at: http://localhost:5030"