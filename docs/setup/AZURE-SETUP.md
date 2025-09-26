# Azure Credentials Setup Guide

## 🚀 Quick Setup Methods

### Method 1: Using the Web Interface (Recommended)

1. **Access your AKS Cost Optimizer**:
   ```bash
   http://localhost:5000
   ```

2. **Navigate to Settings**:
   - Click on **Settings** in the navigation
   - Go to **Azure Configuration** tab

3. **Enter your Azure credentials**:
   - **Azure Tenant ID**: Your Azure AD tenant ID
   - **Azure Subscription ID**: Your Azure subscription ID  
   - **Service Principal Client ID**: Application (client) ID
   - **Service Principal Client Secret**: Client secret value

4. **Test and Save**:
   - Click **"Test Azure Connection"** to verify credentials
   - Click **"Save Azure Settings"** once test passes

### Method 2: Using Environment Variables

**Option A: Set in Docker Run Command**
```bash
docker run -d -p 5000:5000 \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  aks-cost-optimizer:latest
```

**Option B: Create .env File**
```bash
# Create .env file in your project directory
cat > .env << EOF
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
EOF

# Run with .env file
docker run -d -p 5000:5000 --env-file .env aks-cost-optimizer:latest
```

## 📋 Creating Azure Service Principal

### Step 1: Using Azure CLI (Recommended)
```bash
# Login to Azure
az login

# Create service principal with minimal permissions
az ad sp create-for-rbac \
  --name "aks-cost-optimizer" \
  --role "Cost Management Reader" \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID"
```

**Expected Output:**
```json
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "displayName": "aks-cost-optimizer",
  "password": "your-client-secret",
  "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Step 2: Assign Additional Required Permissions
```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Assign Reader role for resource access
az role assignment create \
  --assignee "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --role "Reader" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# Assign Monitoring Reader for metrics
az role assignment create \
  --assignee "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --role "Monitoring Reader" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"
```

### Step 3: Map the Values
From the service principal creation output:
- **AZURE_TENANT_ID** = `tenant` value
- **AZURE_CLIENT_ID** = `appId` value  
- **AZURE_CLIENT_SECRET** = `password` value
- **AZURE_SUBSCRIPTION_ID** = Your subscription ID

## 🔍 Finding Your Azure IDs

### Tenant ID
```bash
az account show --query tenantId -o tsv
```

### Subscription ID
```bash
az account show --query id -o tsv
```

### Via Azure Portal
1. **Tenant ID**: Azure Portal → Azure Active Directory → Properties → Tenant ID
2. **Subscription ID**: Azure Portal → Subscriptions → Your subscription → Subscription ID

## 🛠️ Required Azure Permissions

Your service principal needs these minimum permissions:

| Permission | Scope | Purpose |
|------------|-------|---------|
| **Cost Management Reader** | Subscription | Access cost and billing data |
| **Reader** | Subscription | Access resource information |
| **Monitoring Reader** | Subscription | Access metrics and monitoring data |

## ✅ Testing Your Setup

### Using Web Interface
1. Go to Settings → Azure Configuration
2. Enter your credentials
3. Click **"Test Azure Connection"**
4. Should show: "Azure authentication successful!"

### Using Container Logs
```bash
# Check container logs for authentication status
docker logs aks-cost-optimizer

# Look for these success messages:
# ✅ Azure credentials successfully authenticated
# ✅ Using subscription ID from environment: xxxxxxxx...
```

### Manual Testing
```bash
# Test Azure CLI with your service principal
az login --service-principal \
  -u $AZURE_CLIENT_ID \
  -p $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Test resource access
az resource list --query "length(@)"
```

## 🔒 Security Best Practices

### 1. Principle of Least Privilege
- Only grant minimum required permissions
- Use dedicated service principal for the application
- Regularly rotate client secrets

### 2. Secret Management
- **Never commit secrets to version control**
- Use environment variables or secure secret stores
- Consider Azure Key Vault for production deployments

### 3. Monitoring
- Enable Azure AD sign-in logs
- Monitor service principal usage
- Set up alerts for unusual activity

## 🚨 Troubleshooting

### Common Issues

**1. "ChainedTokenCredential failed to retrieve a token"**
```bash
# Check your credentials are correct
# Verify service principal exists: 
az ad sp show --id $AZURE_CLIENT_ID

# Verify permissions:
az role assignment list --assignee $AZURE_CLIENT_ID
```

**2. "Please run 'az login' to set up an account"**
- This occurs when Azure CLI is not logged in (normal in containers)
- The app should automatically use service principal credentials
- Check environment variables are set correctly

**3. "ManagedIdentityCredential authentication unavailable"**
- This is normal when running outside Azure (containers, local)
- The app will fall back to service principal authentication
- Ensure AZURE_* environment variables are set

### Debug Mode
Enable debug logging to troubleshoot:
```bash
# Add debug environment variable
docker run -d -p 5000:5000 \
  -e LOG_LEVEL=DEBUG \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  aks-cost-optimizer:latest

# Check detailed logs
docker logs aks-cost-optimizer
```

## 📞 Support

If you continue to have authentication issues:

1. **Check Prerequisites**: Ensure your Azure account has the required permissions
2. **Verify Service Principal**: Confirm it exists and has correct role assignments  
3. **Test Manually**: Use Azure CLI to verify credentials work
4. **Check Logs**: Look for specific error messages in container logs
5. **Web Interface**: Use the "Test Azure Connection" button for real-time feedback

For additional support, check the application logs or create an issue with the error details.

---

**Need help?** The web interface provides real-time feedback when testing your Azure connection!