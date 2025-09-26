#!/bin/bash

# AKS Cost Optimizer - Secure Container Build Script
# Builds all three protection variants

set -e

# Check if running from project root
if [ ! -f "main.py" ]; then
    echo "❌ Please run this script from the project root directory:"
    echo "   cd /path/to/aks-cost-optimizer"
    echo "   ./deploy/docker/build-secure-containers.sh"
    exit 1
fi

IMAGE_NAME="aks-cost-optimizer"
TAG="${1:-latest}"

echo "🔒 Building AKS Cost Optimizer with source code protection"
echo "📁 Working from: $(pwd)"
echo "🏷️  Tag: $TAG"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

build_image() {
    local dockerfile=$1
    local variant=$2
    local description=$3
    
    echo -e "${BLUE}🔨 Building $variant variant: $description${NC}"
    echo "   Dockerfile: $dockerfile"
    echo "   Image: ${IMAGE_NAME}-${variant}:${TAG}"
    echo ""
    
    if docker build -f "$dockerfile" -t "${IMAGE_NAME}-${variant}:${TAG}" .; then
        echo -e "${GREEN}✅ Successfully built ${IMAGE_NAME}-${variant}:${TAG}${NC}"
        
        # Get image size
        SIZE=$(docker images "${IMAGE_NAME}-${variant}:${TAG}" --format "table {{.Size}}" | tail -n 1)
        echo -e "${GREEN}   Image size: $SIZE${NC}"
        echo ""
        
        return 0
    else
        echo -e "${RED}❌ Failed to build ${IMAGE_NAME}-${variant}:${TAG}${NC}"
        echo ""
        return 1
    fi
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo "Available build variants:"
echo "1. pyinstaller - Most secure (binary compilation) [DEFAULT]"
echo "2. bytecode    - Good balance (bytecode compilation)" 
echo "3. obfuscated  - Moderate security (code obfuscation)"
echo "4. all         - Build all variants"
echo ""
echo "NOTE: PyInstaller (most secure) is now the default build method!"
echo ""

# Parse command line arguments
VARIANT="${2:-pyinstaller}"

case $VARIANT in
    "pyinstaller"|"1"|"default")
        echo -e "${YELLOW}Building PyInstaller variant (DEFAULT - Most Secure)${NC}"
        build_image "Dockerfile" "default" "Binary compilation - most secure (default)"
        ;;
    "bytecode"|"2")
        echo -e "${YELLOW}Building Bytecode variant only${NC}"
        build_image "deploy/docker/Dockerfile.bytecode" "bytecode" "Bytecode compilation - good balance"
        ;;
    "obfuscated"|"3")
        echo -e "${YELLOW}Building Obfuscated variant only${NC}"
        build_image "deploy/docker/Dockerfile.obfuscated" "obfuscated" "Code obfuscation - moderate security"
        ;;
    "all"|"4")
        echo -e "${YELLOW}Building all variants${NC}"
        echo ""
        
        # Build all variants (default first)
        FAILED=0
        
        build_image "Dockerfile" "default" "Binary compilation - most secure (default)" || FAILED=1
        build_image "deploy/docker/Dockerfile.bytecode" "bytecode" "Bytecode compilation - good balance" || FAILED=1
        build_image "deploy/docker/Dockerfile.obfuscated" "obfuscated" "Code obfuscation - moderate security" || FAILED=1
        
        if [ $FAILED -eq 0 ]; then
            echo -e "${GREEN}🎉 All variants built successfully!${NC}"
        else
            echo -e "${RED}⚠️  Some variants failed to build${NC}"
        fi
        ;;
    *)
        echo -e "${YELLOW}Building PyInstaller variant (DEFAULT - Most Secure)${NC}"
        build_image "Dockerfile" "default" "Binary compilation - most secure (default)"
        ;;
esac

echo ""
echo -e "${BLUE}📋 Built images:${NC}"
docker images | grep "$IMAGE_NAME" | head -10

echo ""
echo -e "${BLUE}🚀 Usage examples:${NC}"
echo ""
echo "Run default variant (PyInstaller - most secure):"
echo "  docker run -d -p 5000:5000 \\"
echo "    -e AZURE_CLIENT_ID=your-client-id \\"
echo "    -e AZURE_CLIENT_SECRET=your-client-secret \\"
echo "    -e AZURE_TENANT_ID=your-tenant-id \\"
echo "    ${IMAGE_NAME}-default:${TAG}"
echo ""
echo "Or with docker-compose (uses default PyInstaller):"
echo "  docker-compose up -d"
echo ""
echo "Run bytecode variant:"
echo "  docker run -d -p 5000:5000 \\"
echo "    -e AZURE_CLIENT_ID=your-client-id \\"
echo "    -e AZURE_CLIENT_SECRET=your-client-secret \\"
echo "    -e AZURE_TENANT_ID=your-tenant-id \\"
echo "    ${IMAGE_NAME}-bytecode:${TAG}"
echo ""
echo "Run obfuscated variant:"
echo "  docker run -d -p 5000:5000 \\"
echo "    -e AZURE_CLIENT_ID=your-client-id \\"
echo "    -e AZURE_CLIENT_SECRET=your-client-secret \\"
echo "    -e AZURE_TENANT_ID=your-tenant-id \\"
echo "    ${IMAGE_NAME}-obfuscated:${TAG}"
echo ""

echo -e "${BLUE}🔍 To verify no source code is exposed:${NC}"
echo "  docker run --rm -it ${IMAGE_NAME}-default:${TAG} ls -la /app  # Should show only binary"
echo "  docker run --rm -it ${IMAGE_NAME}-bytecode:${TAG} find /app -name '*.py' -exec head -5 {} \\;"
echo "  docker run --rm -it ${IMAGE_NAME}-obfuscated:${TAG} head -10 /app/main.py  # Should show obfuscated code"
echo ""

echo -e "${GREEN}✨ Build complete!${NC}"