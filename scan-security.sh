#!/bin/bash

echo "🔍 Running Security Scans..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Scan with Trivy
echo -e "${YELLOW}Running Trivy vulnerability scan...${NC}"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image --severity HIGH,CRITICAL aks-optimizer:prod

# Scan with Snyk (if you have Snyk installed)
if command -v snyk &> /dev/null; then
    echo -e "${YELLOW}Running Snyk scan...${NC}"
    snyk test --docker aks-optimizer:prod --severity-threshold=high
fi

# Check for secrets
echo -e "${YELLOW}Checking for secrets...${NC}"
docker run --rm -v $(pwd):/code trufflesecurity/trufflehog:latest \
    filesystem /code --no-update

# Dockerfile best practices with Hadolint
echo -e "${YELLOW}Linting Dockerfiles...${NC}"
docker run --rm -i hadolint/hadolint < Dockerfile.prod
docker run --rm -i hadolint/hadolint < Dockerfile.dev

echo -e "${GREEN}Security scans complete!${NC}"