# 🔧 Development Guide - AKS Cost Optimizer

## 🚀 **Quick Development Setup**

### **1. Environment Configuration:**
```bash
# Copy development configuration template
cp config/examples/.env.development.example .env

# Edit .env with your actual Azure credentials:
# - AZURE_TENANT_ID
# - AZURE_CLIENT_ID  
# - AZURE_CLIENT_SECRET
# - AZURE_SUBSCRIPTION_ID
```

### **2. Enable Development Mode:**
```bash
# Enable full Enterprise features for development
python3 dev-mode.py enable

# Start your application (dev mode will auto-load)
python3 main.py
```

### **3. Development Server Options:**
```bash
# Standard development server
python3 main.py

# Flask development server with hot reload
FLASK_ENV=development FLASK_DEBUG=true python3 main.py

# Development server with specific port
FLASK_RUN_PORT=5001 python3 main.py
```

### **4. Check Development Status:**
```bash
# See current license status and features
python3 dev-mode.py status
```

### **5. Test Different License Tiers:**
```bash
# Test as FREE tier
python3 dev-mode.py tier --tier free

# Test as PRO tier  
python3 dev-mode.py tier --tier pro

# Test as ENTERPRISE tier
python3 dev-mode.py tier --tier enterprise
```

### **6. Development Configuration Options:**
```bash
# View development configuration
cat .env

# Load development environment variables
export $(cat .env | xargs)

# Check loaded environment
env | grep -E "(AZURE|FLASK|LOG|EMAIL|SLACK)"
```

### **7. Disable Development Mode:**
```bash
# Return to production licensing
python3 dev-mode.py disable
```

## 🎯 **What Changes in Dev Mode:**

### ✅ **Development Mode (Enabled):**
- 🔧 **Red "DEV MODE" indicator** in top-right corner
- 🏢 **Full Enterprise tier** with all features
- 📋 **Implementation Plans** visible and working
- 📊 **Enterprise Metrics** tab visible and working  
- 🔒 **Security Posture** tab visible and working
- 📧 **Email/Slack Alerts** working
- 🤖 **Auto-Analysis** enabled

### 🔒 **Production Mode (Default):**
- 🆓 **FREE tier** by default

## 🔧 **Development Environment Variables**

### **Core Development Settings:**
```bash
# Flask Development
FLASK_ENV=development      # Enable development mode
FLASK_DEBUG=true          # Enable Flask debugger
PRODUCTION_MODE=false     # Disable production optimizations
LOG_LEVEL=DEBUG           # Verbose logging

# Development License
kubeopt_DEV_MODE=true     # Enable full enterprise features
kubeopt_LICENSE_KEY=ENT-dev12345-NEVER

# Development URLs
APP_URL=http://localhost:5001
```

### **Development Analysis Settings:**
```bash
# Faster testing cycles
ANALYSIS_REFRESH_INTERVAL=1    # 1 hour instead of 24
COST_ALERT_THRESHOLD=100       # Lower threshold for testing
AUTO_ANALYSIS_ENABLED=false    # Control background tasks
```

### **Development Notifications:**
```bash
# Test Email (use test accounts)
EMAIL_ENABLED=false
SMTP_USERNAME=test@gmail.com
EMAIL_RECIPIENTS=dev@company.com

# Test Slack (use test workspace)
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TEST/WEBHOOK
SLACK_CHANNEL=#dev-testing
```

### **Development Features:**
```bash
# Enable all enterprise features
ENABLE_MULTI_SUBSCRIPTION=true
PARALLEL_PROCESSING=true
ML_TRAINING_ENABLED=true

# Development debugging
TEST_MODE=true
API_DEBUG_RESPONSES=true
UI_DEBUG_MODE=true
```

## 🧪 **Development Testing**

### **Test Notifications:**
```bash
# Test email configuration
python3 -c "
from infrastructure.services.settings_manager import settings_manager
result = settings_manager.test_email_configuration()
print(result)
"

# Test Slack configuration  
python3 -c "
from infrastructure.services.settings_manager import settings_manager
result = settings_manager.test_slack_integration()
print(result)
"
```

### **Test License Tiers:**
```bash
# Test FREE tier limitations
python3 dev-mode.py tier --tier free
python3 main.py

# Test PRO tier features
python3 dev-mode.py tier --tier pro
python3 main.py

# Test ENTERPRISE tier (full features)
python3 dev-mode.py tier --tier enterprise
python3 main.py
```

### **Test Cost Alerts:**
```bash
# Create test alert with low threshold
# Go to Settings → Alerts Management
# Create alert with $50 threshold for testing
# Trigger with actual cluster analysis
```

## 🔄 **Development Workflow**

### **Daily Development:**
```bash
# 1. Start development session
cp config/examples/.env.development.example .env
python3 dev-mode.py enable

# 2. Start server with hot reload
FLASK_ENV=development FLASK_DEBUG=true python3 main.py

# 3. Access application
open http://localhost:5001

# 4. Check development status
python3 dev-mode.py status
```

### **Feature Testing:**
```bash
# Test different license tiers
python3 dev-mode.py tier --tier free     # Test limitations
python3 dev-mode.py tier --tier pro      # Test PRO features
python3 dev-mode.py tier --tier enterprise  # Test all features

# Test notifications
# Use Settings UI to configure and test email/Slack

# Test cost analysis
# Use lower thresholds in development for easier testing
```

### **Before Committing:**
```bash
# Disable development mode
python3 dev-mode.py disable

# Test in production mode
PRODUCTION_MODE=true python3 main.py

# Verify no development settings committed
git status  # Check no .env files are staged
```

## 🛡️ **Development Security**

### **Environment File Safety:**
- ✅ Use `.env` for development (git-ignored)
- ❌ Never commit `.env` files with real credentials
- ✅ Use separate test accounts for email/Slack
- ✅ Use development Azure subscriptions when possible

### **Development Credentials:**
```bash
# Use separate development credentials
AZURE_TENANT_ID=dev-tenant-id
AZURE_CLIENT_ID=dev-client-id
AZURE_CLIENT_SECRET=dev-client-secret
AZURE_SUBSCRIPTION_ID=dev-subscription-id

# Use test notification accounts
SMTP_USERNAME=dev-test@gmail.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/DEV/TEST/WEBHOOK
```
- 🚫 **Premium tabs completely hidden** (not just locked)
- 📊 **Only Dashboard** visible
- 🔒 **Feature lock system** active

## 📱 **UI Behavior:**

### **Hidden vs Locked Features:**
- **🚫 HIDDEN**: Premium tabs are completely invisible in FREE tier
- **🔒 LOCKED**: If you want to show but disable, use `lockFeature()` instead of `hideFeature()`

### **Upgrade Prompts:**
- **🎯 Click locked features** → Shows upgrade modal
- **💡 Navigation shows tier badge** → FREE/PRO/ENTERPRISE
- **⚡ Upgrade banner** appears for FREE tier users

## ⚙️ **Environment Variables:**

### **Manual Override:**
```bash
# Set specific license key
export kubeopt_LICENSE_KEY="PRO-test1234-NEVER"

# Force development mode
export kubeopt_DEV_MODE="true"

# Bypass all licensing (full access)
export kubeopt_BYPASS_LICENSE="true"
```

### **File-based (.env.development):**
```bash
# The dev-mode.py script creates this automatically
kubeopt_LICENSE_KEY=ENT-dev12345-NEVER
kubeopt_DEV_MODE=true
```

## 🧪 **Testing License Keys:**

### **Trial License Format:**
```
PRO-xxxxxxxx-20251201    # 30-day Pro trial
ENT-xxxxxxxx-20251201    # 30-day Enterprise trial
FREE-xxxxxxxx-NEVER      # Free tier (default)
```

### **Development Keys:**
```
ENT-dev12345-NEVER       # Never expires Enterprise
PRO-dev12345-NEVER       # Never expires Pro
```

## 🔍 **Debugging:**

### **Check License Loading:**
```bash
# See detailed license status
python3 dev-mode.py status
```

### **Browser Console:**
```javascript
// Check feature flags in browser
console.log(window.featureLockManager.featureFlags);

// Check license info
console.log(window.featureLockManager.licenseInfo);

// Test feature access
console.log(checkFeatureAccess('implementation_plan'));
```

### **API Endpoints:**
```bash
# Check license via API
curl http://localhost:5000/api/license/info

# Test protected endpoint (should work in dev mode)
curl http://localhost:5000/api/implementation-plan?cluster_id=test
```

## 📂 **File Structure:**
```
.env.development          # Auto-created by dev-mode.py
dev-mode.py              # Development utility script  
infrastructure/services/
├── license_manager.py   # Core licensing (with dev mode support)
└── feature_guard.py     # Feature protection decorators
presentation/web/static/
├── js/feature-lock.js   # Frontend feature hiding/locking
└── css/feature-lock.css # UI styling for locks/badges
```

## 🎯 **Workflow:**

### **Development:**
1. `python3 dev-mode.py enable` → Full access
2. Work on all features freely
3. Test implementation plans, enterprise metrics, etc.

### **Testing Tiers:**
1. `python3 dev-mode.py tier --tier free` → Test FREE experience
2. Check that premium tabs are hidden
3. `python3 dev-mode.py tier --tier pro` → Test PRO experience  
4. `python3 dev-mode.py tier --tier enterprise` → Test ENTERPRISE experience

### **Production:**
1. `python3 dev-mode.py disable` → Production mode
2. Deploy without .env.development file
3. Customers use license keys or trials

---

**🚀 Perfect for container deployment!** The licensing system is self-contained and works in any environment.