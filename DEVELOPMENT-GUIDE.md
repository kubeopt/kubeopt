# 🔧 Development Mode Guide

## 🚀 **Quick Setup for Full Features**

### **Enable Development Mode:**
```bash
# Enable full Enterprise features for development
python3 dev-mode.py enable

# Start your application (dev mode will auto-load)
python3 main.py
```

### **Check Status:**
```bash
# See current license status and features
python3 dev-mode.py status
```

### **Test Different Tiers:**
```bash
# Test as FREE tier
python3 dev-mode.py tier --tier free

# Test as PRO tier  
python3 dev-mode.py tier --tier pro

# Test as ENTERPRISE tier
python3 dev-mode.py tier --tier enterprise
```

### **Disable Development Mode:**
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
export KUBEVISTA_LICENSE_KEY="PRO-test1234-NEVER"

# Force development mode
export KUBEVISTA_DEV_MODE="true"

# Bypass all licensing (full access)
export KUBEVISTA_BYPASS_LICENSE="true"
```

### **File-based (.env.development):**
```bash
# The dev-mode.py script creates this automatically
KUBEVISTA_LICENSE_KEY=ENT-dev12345-NEVER
KUBEVISTA_DEV_MODE=true
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