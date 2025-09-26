# AKS Cost Optimizer - Secure Container Deployment

This document explains how to deploy the AKS Cost Optimizer with source code protection. **PyInstaller binary compilation is now the default method** for maximum security.

## 🔒 Security Approaches

### 1. PyInstaller Binary (Default - Most Secure) ⭐
- **File**: `Dockerfile` (default)
- **Security**: Highest - compiles to standalone binary
- **Size**: Largest (includes Python runtime)
- **Debug**: No debugging capabilities
- **Use case**: Production deployments, IP protection (DEFAULT)

### 2. Bytecode Compilation (Alternative)
- **File**: `Dockerfile.bytecode`
- **Security**: Good balance of protection and maintainability
- **Size**: Medium (smallest of the three)
- **Debug**: Limited debugging capabilities
- **Use case**: When you need smaller images but still want protection

### 3. Code Obfuscation (Alternative)
- **File**: `Dockerfile.obfuscated`  
- **Security**: Moderate - code is obfuscated but still Python
- **Size**: Similar to bytecode
- **Debug**: Some debugging capabilities remain
- **Use case**: When you need debugging but want basic protection

## 🚀 Quick Start

### Method 1: Default Build (Recommended)
```bash
# Build default (PyInstaller - most secure)
docker build -t aks-cost-optimizer:latest .

# Or use docker-compose (uses default Dockerfile)
docker-compose up -d
```

### Method 2: Build Script (All Variants)
```bash
# Build default only (PyInstaller)
./build-secure-containers.sh

# Build all variants
./build-secure-containers.sh latest all

# Build specific alternative variant
./build-secure-containers.sh latest bytecode
```

### Method 3: Alternative Variants
```bash
# Bytecode variant
docker build -f Dockerfile.bytecode -t aks-cost-optimizer-bytecode:latest .

# Obfuscated variant
docker build -f Dockerfile.obfuscated -t aks-cost-optimizer-obfuscated:latest .

# Multi-variant deployment
docker-compose -f docker-compose.secure.yml up
```

## 🔧 Configuration

### Required Environment Variables
```bash
AZURE_CLIENT_ID=your-service-principal-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_TENANT_ID=your-tenant-id
```

### Optional Environment Variables
```bash
AZURE_SUBSCRIPTION_ID=specific-subscription-id
FLASK_SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

## 🏃 Running Containers

### Single Container
```bash
docker run -d \
  --name aks-optimizer \
  -p 5000:5000 \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_TENANT_ID=your-tenant-id \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/infrastructure/persistence/database:/app/infrastructure/persistence/database \
  aks-cost-optimizer-bytecode:latest
```

### With Docker Compose
```bash
# All variants on different ports
docker-compose -f docker-compose.secure.yml up -d

# Access via:
# Bytecode:    http://localhost:5001
# PyInstaller: http://localhost:5002  
# Obfuscated:  http://localhost:5003
```

## 🔍 Verification

### Check Source Code Protection
```bash
# Bytecode - should show compiled bytecode, not source
docker run --rm -it aks-cost-optimizer-bytecode:latest find /app -name "*.py" -exec head -5 {} \;

# PyInstaller - should show only binary, no Python files
docker run --rm -it aks-cost-optimizer-pyinstaller:latest ls -la /app

# Obfuscated - should show obfuscated code
docker run --rm -it aks-cost-optimizer-obfuscated:latest head -10 /app/main.py
```

### Container Security Scan
```bash
# Scan for vulnerabilities (if you have docker scout)
docker scout cves aks-cost-optimizer-bytecode:latest
```

## 📊 Comparison Matrix

| Feature | PyInstaller (Default) | Bytecode | Obfuscated |
|---------|----------------------|----------|------------|
| **Security Level** | Highest ⭐ | Good | Moderate |
| **Image Size** | Large | Small | Medium |
| **Build Time** | Slow | Fast | Medium |
| **Runtime Performance** | Good | Best | Good |
| **Debugging** | None | Limited | Some |
| **Recommended For** | Production (Default) | Small Images | Development |
| **Default Status** | ✅ DEFAULT | Alternative | Alternative |

## 🛡️ Security Best Practices

### 1. Service Principal Security
- Use dedicated service principal with minimal permissions
- Rotate credentials regularly
- Store credentials in secure secret management

### 2. Container Security
- Run containers as non-root user (already configured)
- Use read-only file systems where possible
- Implement network policies
- Regular security scanning

### 3. Deployment Security
```bash
# Use secrets management instead of environment variables
docker run -d \
  --name aks-optimizer \
  -p 5000:5000 \
  --secret azure_client_id \
  --secret azure_client_secret \
  --secret azure_tenant_id \
  aks-cost-optimizer-bytecode:latest
```

## 🐛 Troubleshooting

### Common Issues

1. **PyInstaller build fails**
   - Increase Docker memory allocation
   - Check hidden imports in spec file

2. **Bytecode runtime errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

3. **Obfuscation breaks code**
   - Some dynamic imports may fail
   - Consider excluding specific modules

### Debug Mode
```bash
# Enable debug mode (reduces security)
docker run --rm -it \
  -e FLASK_DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  aks-cost-optimizer-bytecode:latest
```

## 📝 License & Legal

- This source code protection is for intellectual property protection
- Ensure compliance with your organization's security policies
- The protection methods are defensive measures, not absolute security

## 🤝 Support

For issues with secure containers:
1. Check container logs: `docker logs container-name`
2. Verify environment variables are set correctly
3. Test with original Dockerfile first
4. Open issue with specific error messages