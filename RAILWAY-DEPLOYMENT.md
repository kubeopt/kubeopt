# Railway Deployment Guide for KubeOpt

This guide provides step-by-step instructions for deploying KubeOpt to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: KubeOpt code should be pushed to a GitHub repository
3. **Azure Service Principal**: Follow the [SERVICE-PRINCIPAL-SETUP.md](docs/SERVICE-PRINCIPAL-SETUP.md) guide

## Deployment Steps

### 1. Create New Railway Project

1. Log into Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your KubeOpt repository
5. Railway will automatically detect the `railway.toml` configuration

### 2. Configure Environment Variables

In the Railway dashboard, go to your project settings and add these environment variables:

#### Required Azure Configuration
```bash
AZURE_CLIENT_ID=your-service-principal-client-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
AZURE_TENANT_ID=your-azure-tenant-id
```

#### Application Settings
```bash
FLASK_ENV=production
PRODUCTION_MODE=true
LOG_LEVEL=INFO
DATABASE_PATH=/app/data/aks_optimizer.db
AZURE_CONFIG_DIR=/app/.azure
```

#### Optional Settings
```bash
# Slack Integration (optional)
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=
SLACK_CHANNEL=
SLACK_COST_THRESHOLD=1500

# Email Settings (optional)
EMAIL_ENABLED=false
SMTP_SERVER=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
FROM_EMAIL=
EMAIL_RECIPIENTS=

# Auto Analysis
AUTO_ANALYSIS_ENABLED=true
AUTO_ANALYSIS_INTERVAL=120m
COST_ALERT_THRESHOLD=500
COST_CACHE_HOURS=6

# Database Cleanup
DATABASE_CLEANUP_ENABLED=true
DATABASE_CLEANUP_INTERVAL_HOURS=24
DATABASE_RETENTION_DAYS=90

# License (if using enterprise features)
KUBEOPT_LICENSE_KEY=your-license-key
LICENSE_API_URL=https://license.kubeopt.com

# Session Settings
SESSION_TIMEOUT=120
USER_USERNAME=admin
USER_PASSWORD_HASH=your-password-hash
USER_ROLE=admin
```

### 3. Deploy

1. Railway will automatically start building and deploying
2. The build process uses `Dockerfile.railway` for optimized Railway deployment
3. Health checks are configured to use `/health` endpoint
4. Deployment typically takes 3-5 minutes

### 4. Access Your Application

1. Once deployed, Railway provides a public URL (e.g., `https://your-app.railway.app`)
2. Access your KubeOpt instance at this URL
3. Login with your configured credentials

### 5. Verify Deployment

1. Check health endpoint: `https://your-app.railway.app/health`
2. Verify Azure connectivity in Settings page
3. Add your first AKS cluster for analysis

## Configuration Files

### railway.toml
```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300

[env]
PORT = "5010"
FLASK_ENV = "production"
PYTHONUNBUFFERED = "1"
PYTHONPATH = "/app"
DATABASE_PATH = "/app/data/aks_optimizer.db"
AZURE_CONFIG_DIR = "/app/.azure"
```

### Dockerfile.railway
- Optimized multi-stage build for Railway
- Includes gunicorn for production WSGI server
- Health check configuration
- Non-root user security
- Volume persistence for database

### wsgi.py
- Production WSGI entry point
- Compatible with gunicorn
- Proper application factory pattern

## Troubleshooting

### Common Issues

#### 1. Build Failures
- **Issue**: Dockerfile not found
- **Solution**: Ensure `Dockerfile.railway` is in repository root
- **Alternative**: Rename to `Dockerfile` if Railway can't find it

#### 2. Environment Variables
- **Issue**: Azure authentication fails
- **Solution**: Double-check all Azure environment variables are set correctly
- **Check**: Ensure service principal has proper permissions

#### 3. Health Check Failures
- **Issue**: Railway shows service as unhealthy
- **Solution**: Check `/health` endpoint returns 200 status
- **Debug**: Check Railway logs for startup errors

#### 4. Database Issues
- **Issue**: Data not persisting between deployments
- **Solution**: Ensure `DATABASE_PATH` points to `/app/data/` directory
- **Note**: Railway provides ephemeral storage - data may be lost on redeploys

### Log Access

View deployment logs in Railway dashboard:
1. Go to your project
2. Click "Deployments" tab
3. Click on latest deployment
4. View "Build Logs" and "Runtime Logs"

### Custom Domain

To use a custom domain:
1. Go to Railway project settings
2. Click "Domains" tab
3. Add your custom domain
4. Configure DNS records as instructed

## Production Considerations

### 1. Database Persistence
- Railway provides ephemeral storage
- Consider using external database (PostgreSQL, MySQL) for production
- Update database connection settings accordingly

### 2. Monitoring
- Enable Railway's built-in monitoring
- Set up external monitoring (DataDog, New Relic, etc.)
- Configure alerts for downtime

### 3. Security
- Use Railway's environment variable encryption
- Rotate service principal secrets regularly
- Enable IP whitelisting if needed

### 4. Scaling
- Railway handles auto-scaling based on traffic
- Monitor resource usage in dashboard
- Upgrade plan if needed for higher limits

### 5. Backups
- Implement database backup strategy
- Export configuration settings regularly
- Document disaster recovery procedures

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_CLIENT_ID` | ✅ | - | Service principal client ID |
| `AZURE_CLIENT_SECRET` | ✅ | - | Service principal secret |
| `AZURE_SUBSCRIPTION_ID` | ✅ | - | Primary Azure subscription |
| `AZURE_TENANT_ID` | ✅ | - | Azure AD tenant ID |
| `FLASK_ENV` | ❌ | development | Flask environment |
| `PRODUCTION_MODE` | ❌ | false | Enable production features |
| `LOG_LEVEL` | ❌ | WARNING | Logging level |
| `AUTO_ANALYSIS_ENABLED` | ❌ | false | Enable background analysis |
| `COST_ALERT_THRESHOLD` | ❌ | 500 | Cost alert threshold (USD) |
| `DATABASE_CLEANUP_ENABLED` | ❌ | true | Enable database cleanup |
| `SESSION_TIMEOUT` | ❌ | 120 | Session timeout (minutes) |

## Support

- GitHub Issues: [Create an issue](https://github.com/your-org/kubeopt/issues)
- Documentation: [docs/](docs/)
- Architecture Guide: [docs/ARCHITECTURE-GUIDE.md](docs/ARCHITECTURE-GUIDE.md)

---

**Note**: This deployment uses Railway's free tier limitations. For production workloads, consider upgrading to a paid plan for better performance and reliability.