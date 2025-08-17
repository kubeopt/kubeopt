#!/bin/bash
# Quick fix script for Azure CLI read-only filesystem issue

set -e

echo "🔧 Fixing Azure CLI authentication issue..."

# Step 1: Create the entrypoint script
echo "📝 Creating docker-entrypoint.sh..."
cat > docker-entrypoint.sh << 'EOF'
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
EOF

chmod +x docker-entrypoint.sh

# Step 2: Update Dockerfile to add the entrypoint
echo "📝 Updating Dockerfile..."
if ! grep -q "docker-entrypoint.sh" Dockerfile 2>/dev/null; then
    # Add entrypoint script copy before the USER directive
    sed -i.bak '/^USER appuser/i \
# Copy entrypoint script\
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/\
RUN chmod +x /usr/local/bin/docker-entrypoint.sh\
' Dockerfile

    # Add ENTRYPOINT at the end, before CMD
    sed -i.bak '/^CMD/i \
# Use entrypoint script\
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]\
' Dockerfile
fi

# Step 3: Update docker-compose.yml
echo "📝 Updating docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
services:
  aks-optimizer:
    build: 
      context: .
      dockerfile: Dockerfile
    image: aks-optimizer:latest
    container_name: aks-cost-optimizer
    
    ports:
      - "5020:5000"
    
    volumes:
      # Mount app for development
      - ./app:/app/app:cached
      
      # Data persistence
      - sqlite_data:/app/data
      - ml_models:/app/models
      - app_logs:/app/logs
      - app_cache:/app/cache
      
      # Mount Azure credentials to temp location for copying
      - ${HOME}/.azure:/tmp/host-azure:ro
      
      # Writable Azure config directory
      - azure_config:/home/appuser/.azure
      
    environment:
      # Flask settings
      - FLASK_ENV=${FLASK_ENV:-development}
      - FLASK_DEBUG=${FLASK_DEBUG:-1}
      - DATABASE_PATH=/app/data/aks_optimizer.db
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - PYTHONPATH=/app
      
      # Azure settings
      - AZURE_CONFIG_DIR=/home/appuser/.azure
      - AZURE_CORE_COLLECT_TELEMETRY=false
      
      # Enable multi-subscription support
      - ENABLE_MULTI_SUBSCRIPTION=true
      - PARALLEL_PROCESSING=true
      
    restart: unless-stopped
    
    networks:
      - aks-network
    
    user: "1000:1000"
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  sqlite_data:
    driver: local
  ml_models:
    driver: local
  app_logs:
    driver: local
  app_cache:
    driver: local
  azure_config:
    driver: local

networks:
  aks-network:
    driver: bridge
EOF

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