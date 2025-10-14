# AKS Cost Optimizer - Quick Start

## 🚀 Immediate Setup

### 1. Build & Run (Most Secure)
```bash
# Build with PyInstaller (default - most secure)
docker build -t aks-cost-optimizer .

# Run with Azure credentials and optional notifications
docker run -d -p 5000:5000 \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  -e EMAIL_ENABLED=true \
  -e SMTP_USERNAME=your-email@domain.com \
  -e SMTP_PASSWORD=your-password \
  -e SLACK_ENABLED=true \
  -e SLACK_WEBHOOK_URL=your-webhook-url \
  aks-cost-optimizer
```

### 2. Access Your Tool
```
http://localhost:5000
```

### 3. Configure Azure Credentials
1. Go to **Settings** → **Azure Configuration**
2. Enter your Azure credentials
3. Click **"Test Azure Connection"**
4. Click **"Save Azure Settings"**

### 4. Optional: Configure Notifications
1. Go to **Settings** → **Slack Integration**
   - Enable Slack Notifications
   - Add Slack Webhook URL
   - Set Default Channel (e.g., `#aks-cost-alerts`)
   
2. Go to **Settings** → **Email Settings**
   - Enable Email Notifications
   - Configure SMTP Settings
   - Add Recipients

3. **Test Notifications:**
   - Create a test alert in Alerts Management
   - Use "Test Alert" button to verify notifications work

## 📋 Alternative Options

### Development Mode (Local)
```bash
# Setup development environment
cp config/examples/.env.development.example .env.local
python3 dev-mode.py enable

# Start development server
FLASK_ENV=development python3 main.py
```

### Development Mode (Docker)
```bash
docker-compose up -d
```

### Build All Secure Variants
```bash
./deploy/docker/build-secure-containers.sh latest all
```

### Production Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Documentation

- **Azure Setup**: [`docs/setup/AZURE-SETUP.md`](docs/setup/AZURE-SETUP.md)
- **Container Security**: [`docs/deployment/README.secure-containers.md`](docs/deployment/README.secure-containers.md)
- **Project Structure**: [`docs/PROJECT-STRUCTURE.md`](docs/PROJECT-STRUCTURE.md)

## 🔧 Troubleshooting

**Azure Auth Issues?** → Check [`docs/setup/AZURE-SETUP.md`](docs/setup/AZURE-SETUP.md)  
**Container Issues?** → Check [`docs/deployment/README.secure-containers.md`](docs/deployment/README.secure-containers.md)  
**Build Issues?** → Run from project root: `./deploy/docker/build-secure-containers.sh`

---
**Need help?** Use the web interface Settings page for real-time Azure connection testing!