# Docker Configuration for Config Files

## Dockerfile additions:

```dockerfile
# Copy config files to container
COPY config/ /app/config/

# Set environment variable for config directory
ENV CONFIG_DIR=/app/config

# Optional: Create config directory if it doesn't exist
RUN mkdir -p /app/config
```

## Docker run example:

```bash
# Option 1: Use built-in config
docker run your-aks-optimizer

# Option 2: Override config directory
docker run -e CONFIG_DIR=/custom/config -v /host/config:/custom/config your-aks-optimizer

# Option 3: Mount specific config files
docker run -v /host/config:/app/config your-aks-optimizer
```

## Environment Variables:

- `CONFIG_DIR` - Directory containing config files (default: auto-detected)
- Files expected in CONFIG_DIR:
  - `scoring.yaml` (cloud-agnostic base)
  - `implementation_standards.yaml` (cloud-agnostic base)
  - `azure_scoring.yaml` (optional Azure overlay)

## Development vs Production:

**Development (no CONFIG_DIR set):**
- Auto-detects config from project structure
- Uses relative paths from source code

**Production (CONFIG_DIR set):**
- Uses absolute path from environment variable
- Works in containers, packaged apps, etc.