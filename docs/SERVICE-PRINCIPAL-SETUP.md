# Service Principal Setup Guide for AKS Cost Optimizer

This guide provides comprehensive instructions for setting up an Azure Service Principal with the correct permissions for AKS Cost Optimizer to function across your organization.

## Table of Contents
- [Overview](#overview)
- [Service Principal Creation](#service-principal-creation)
- [Required Permissions](#required-permissions)
- [Organization-Wide Access Setup](#organization-wide-access-setup)
- [Application Configuration](#application-configuration)
- [Validation and Testing](#validation-and-testing)
- [Troubleshooting](#troubleshooting)

## Overview

AKS Cost Optimizer requires a Service Principal with appropriate permissions to:
- Access AKS clusters across subscriptions
- Execute kubectl commands via Azure CLI
- Retrieve cost and billing information
- Monitor cluster resources and metrics
- Generate optimization recommendations

## Service Principal Creation

### Method 1: Azure CLI (Recommended)
```bash
# Create service principal with basic Reader role
az ad sp create-for-rbac \
  --name "aks-cost-optimizer" \
  --role "Reader" \
  --scopes "/subscriptions/{subscription-id}" \
  --output json

# Output will be:
# {
#   "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#   "displayName": "aks-cost-optimizer",
#   "password": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#   "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
# }
```

### Method 2: Azure Portal
1. Navigate to **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Name: `aks-cost-optimizer`
4. Click **Register**
5. Note the **Application (client) ID** and **Directory (tenant) ID**
6. Go to **Certificates & secrets** > **New client secret**
7. Create and save the secret value

## Required Permissions

### Core Permissions (Organization-Wide)

#### 1. Organization-Level Permissions (Recommended)
Apply these roles at the **management group level** to cover all subscriptions:

```bash
SP={service-principal-id}
MG={management-group-id}

for role in "Reader" "Cost Management Reader" \
           "Monitoring Reader" \
           "Azure Kubernetes Service RBAC Reader"; do
  az role assignment create --assignee $SP --role "$role" \
    --scope "/providers/Microsoft.Management/managementGroups/$MG"
done
```

To find your management group ID: `az account management-group list --output table`

| Role | Purpose |
|------|---------|
| Reader | Basic read access to resources |
| Cost Management Reader | Access cost and billing data |
| Monitoring Reader | Access metrics and monitoring data |
| Azure Kubernetes Service RBAC Reader | AKS cluster metadata access |

**Alternative: Per-subscription scope** (if management group access is not available):

```bash
SP={service-principal-id}
SUB={subscription-id}

for role in "Reader" "Cost Management Reader" \
           "Monitoring Reader" \
           "Azure Kubernetes Service RBAC Reader"; do
  az role assignment create --assignee $SP --role "$role" \
    --scope "/subscriptions/$SUB"
done
```

#### 2. AKS-Specific Permissions
For each AKS cluster or resource group:

```bash
# STEP 1: Create custom role for kubectl runCommand operations (REQUIRED)
# Built-in roles do NOT include runCommand permissions
az role definition create --role-definition '{
  "Name": "AKS Run Command Role",
  "Description": "Custom role for AKS kubectl run command operations",
  "Actions": [
    "Microsoft.ContainerService/managedClusters/read",
    "Microsoft.ContainerService/managedClusters/runcommand/action",
    "Microsoft.ContainerService/managedclusters/commandResults/read"
  ],
  "AssignableScopes": ["/subscriptions/{subscription-id}"]
}'

# STEP 2: Assign cluster-level roles (per cluster or per resource group)
CLUSTER_SCOPE="/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.ContainerService/managedClusters/{cluster}"

for role in "AKS Run Command Role" \
           "Azure Kubernetes Service Cluster User Role" \
           "Azure Kubernetes Service RBAC Cluster Admin"; do
  az role assignment create --assignee $SP --role "$role" \
    --scope "$CLUSTER_SCOPE"
done

# Alternative: Apply to entire resource group (recommended for multiple clusters)
RG_SCOPE="/subscriptions/{sub-id}/resourceGroups/{rg}"

for role in "AKS Run Command Role" \
           "Azure Kubernetes Service Cluster User Role" \
           "Azure Kubernetes Service RBAC Cluster Admin"; do
  az role assignment create --assignee $SP --role "$role" \
    --scope "$RG_SCOPE"
done
```

**⚠️ IMPORTANT NOTES**: 
1. The `runCommand` permissions are NOT included in any built-in Azure roles as of 2024-2025. The custom role above is **REQUIRED** for kubectl operations to work through Azure's runCommand API.
2. The runCommand feature creates temporary pods with resource requirements (200m CPU, 500Mi memory requests). See [Resource Requirements](#runcommand-resource-requirements) section below.
3. **Azure Kubernetes Service RBAC Cluster Admin** is REQUIRED for clusters with Azure RBAC integration enabled. This grants Kubernetes cluster-admin permissions through Azure RBAC instead of traditional Kubernetes RBAC.

#### 3. Management Group Level (Enterprise Setup)

See [Organization-Level Permissions](#1-organization-level-permissions-recommended) above — management group scope is now the recommended default for all 4 core roles (Reader, Cost Management Reader, Monitoring Reader, AKS RBAC Reader).

### Advanced Permissions (Optional)

#### For Enhanced Optimization Features:
```bash
# Contributor access to specific resource groups (for applying optimizations)
az role assignment create \
  --assignee {service-principal-id} \
  --role "Contributor" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"

# Network access for advanced networking analysis
az role assignment create \
  --assignee {service-principal-id} \
  --role "Network Contributor" \
  --scope "/subscriptions/{subscription-id}"
```

## Organization-Wide Access Setup

### Multi-Subscription Architecture Overview

**⚠️ IMPORTANT**: For organizations with multiple Azure subscriptions (dev, UAT, staging, DR, prod), you need **only ONE service principal** that can access all subscriptions within the same Azure AD tenant.

#### Service Principal Scope Across Subscriptions

According to Microsoft documentation: *"If you have multiple Azure Subscriptions in one Azure AD tenant you may use your single Service Principal across all of your Azure Subscriptions."*

```
Organization A (Single Azure AD Tenant)
├── Dev Subscription 1 ────┐
├── Dev Subscription 2 ────┤
├── UAT Subscription 1 ────┤
├── UAT Subscription 2 ────┤    → Single KubeOpt Service Principal
├── Stage Subscription ────┤      (Role assigned to each subscription)
├── DR Subscription ───────┤
└── Prod Subscription ─────┘
```

#### Benefits of Single Service Principal Approach

**✅ Operational Benefits:**
- **Single authentication** - easier credential management
- **Consistent permissions** across all environments
- **Simplified onboarding** - create one SP, assign to all subscriptions
- **One secret to rotate** instead of multiple per subscription

**✅ Security Benefits:**
- **Least privilege** - only Reader + AKS User roles required
- **Scoped per subscription** - can revoke access selectively
- **Audit trail** - clear ownership and tracking
- **Standard enterprise pattern** - used by monitoring tools like Datadog, New Relic

**✅ Architectural Benefits:**
- **Centralized configuration** in KubeOpt application
- **Easy troubleshooting** - single identity to debug
- **Scalable** - automatically works with new subscriptions

#### Implementation Strategy

**Step 1: Create Single Service Principal (One Time)**
```bash
# Organization creates ONE service principal for all subscriptions
az ad sp create-for-rbac --name "kubeopt-analyzer" --skip-assignment

# Output: 
# {
#   "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#   "displayName": "kubeopt-analyzer", 
#   "password": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#   "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
# }
```

**Step 2: Apply Permissions Per Subscription**
Use the automation script below to assign roles to each subscription systematically.

### For Multiple Subscriptions
Create a script to apply permissions across all subscriptions:

```bash
#!/bin/bash
# setup-org-wide-permissions.sh

SERVICE_PRINCIPAL_ID="your-service-principal-app-id"
SUBSCRIPTIONS=(
    "subscription-id-1"
    "subscription-id-2"
    "subscription-id-3"
    # Add all your subscription IDs
)

echo "Setting up organization-wide permissions for Service Principal: $SERVICE_PRINCIPAL_ID"

for SUB_ID in "${SUBSCRIPTIONS[@]}"; do
    echo "Configuring subscription: $SUB_ID"
    
    # Set subscription context
    az account set --subscription $SUB_ID
    
    # Core permissions
    az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "Reader" --scope "/subscriptions/$SUB_ID"
    az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "Cost Management Reader" --scope "/subscriptions/$SUB_ID"
    az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "Monitoring Reader" --scope "/subscriptions/$SUB_ID"
    az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "Azure Kubernetes Service RBAC Reader" --scope "/subscriptions/$SUB_ID"
    
    # Create AKS Run Command custom role (only needs to be created once per subscription)
    az role definition create --role-definition "{
      \"Name\": \"AKS Run Command Role\",
      \"Description\": \"Custom role for AKS kubectl run command operations\",
      \"Actions\": [
        \"Microsoft.ContainerService/managedClusters/read\",
        \"Microsoft.ContainerService/managedClusters/runcommand/action\",
        \"Microsoft.ContainerService/managedclusters/commandResults/read\"
      ],
      \"AssignableScopes\": [\"/subscriptions/$SUB_ID\"]
    }" 2>/dev/null || echo "Custom role already exists or creation failed"
    
    # Apply AKS permissions to all clusters in subscription
    az aks list --query "[].{name:name,resourceGroup:resourceGroup}" --output tsv | while read name resourceGroup; do
        if [ ! -z "$name" ] && [ ! -z "$resourceGroup" ]; then
            echo "Applying AKS permissions to cluster: $name in $resourceGroup"
            az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "AKS Run Command Role" --scope "/subscriptions/$SUB_ID/resourceGroups/$resourceGroup/providers/Microsoft.ContainerService/managedClusters/$name"
            az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "Azure Kubernetes Service Cluster User Role" --scope "/subscriptions/$SUB_ID/resourceGroups/$resourceGroup/providers/Microsoft.ContainerService/managedClusters/$name"
            az role assignment create --assignee $SERVICE_PRINCIPAL_ID --role "Azure Kubernetes Service RBAC Cluster Admin" --scope "/subscriptions/$SUB_ID/resourceGroups/$resourceGroup/providers/Microsoft.ContainerService/managedClusters/$name"
        fi
    done
    
    echo "Subscription $SUB_ID configured successfully"
done

echo "Organization-wide setup complete!"
```

### For All AKS Clusters
Script to apply AKS-specific permissions:

```bash
#!/bin/bash
# setup-aks-permissions.sh

SERVICE_PRINCIPAL_ID="your-service-principal-app-id"

# Get all AKS clusters across all subscriptions
az account list --query "[].id" --output tsv | while read SUB_ID; do
    echo "Processing subscription: $SUB_ID"
    az account set --subscription $SUB_ID
    
    # Get all AKS clusters in this subscription
    az aks list --query "[].{name:name,resourceGroup:resourceGroup,id:id}" --output json | jq -r '.[] | "\(.id)"' | while read CLUSTER_ID; do
        echo "Applying permissions to cluster: $CLUSTER_ID"
        
        az role assignment create \
            --assignee $SERVICE_PRINCIPAL_ID \
            --role "Azure Kubernetes Service RBAC Reader" \
            --scope "$CLUSTER_ID"
    done
done
```

## Application Configuration

### Logical Flow in AKS Cost Optimizer

The application follows this flow for service principal setup:

```
1. Frontend Form (Settings Page)
   ├── Azure Tenant ID
   ├── Azure Subscription ID
   ├── Service Principal Client ID
   └── Service Principal Client Secret

2. Form Submission
   ├── save_settings() endpoint
   ├── Settings Manager processes data
   └── Converts to environment variables

3. Backend Processing
   ├── Updates .env file
   ├── Refreshes Azure SDK Manager
   └── Validates subscription access

4. Azure SDK Manager
   ├── Initializes credential chain
   ├── Tests authentication
   └── Caches successful connections
```

### Configuration Steps

1. **Navigate to Settings**
   - Go to Settings → Azure Configuration tab

2. **Enter Service Principal Details**
   - **Azure Tenant ID**: Your Azure AD tenant ID
   - **Azure Subscription ID**: Primary subscription (can access others via SDK)
   - **Service Principal Client ID**: Application ID from service principal
   - **Service Principal Client Secret**: Secret key generated

3. **Test Connection**
   - Click "Test Azure Connection"
   - Should return: "Azure authentication successful! Connected to subscription: xxxxxxxx..."

4. **Save Configuration**
   - Click "Save Azure Settings"
   - Settings are persisted to `.env` file
   - Azure credentials are automatically refreshed

### Environment Variables Created
```bash
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_SUBSCRIPTION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Validation and Testing

### 1. Test Service Principal Authentication
```bash
# Test login with service principal
az login --service-principal \
  --username {client-id} \
  --password {client-secret} \
  --tenant {tenant-id}

# Verify access to subscriptions
az account list --output table
```

### 2. Test AKS Access
```bash
# List all AKS clusters
az aks list --output table

# Test kubectl access to a cluster
az aks get-credentials --resource-group {rg-name} --name {cluster-name}
kubectl get nodes
```

### 3. Test Cost Management Access
```bash
# Test cost data retrieval
az consumption usage list --top 5
```

### 4. Application-Level Testing
1. **In AKS Cost Optimizer Settings:**
   - Use "Test Azure Connection" button
   - Should show green success message

2. **Add a Cluster:**
   - Try adding an AKS cluster
   - Should successfully connect and retrieve data

3. **Check Logs:**
   ```bash
   # Look for successful authentication logs
   grep "Azure authentication successful" logs/app.log
   ```

## RunCommand Resource Requirements

### Understanding AKS RunCommand Limitations

The Azure `runCommand` feature creates temporary pods to execute kubectl commands. These pods have specific resource requirements:

- **CPU Request**: 200m (0.2 CPU cores)
- **Memory Request**: 500Mi (500 MiB)
- **CPU Limit**: 500m (0.5 CPU cores) 
- **Memory Limit**: 1Gi (1 GiB)

### Common Resource Issues

#### Issue: "Insufficient resources for the RunCommand pod"
```
(KubernetesPerformanceError) Pod is not schedulable: Insufficient resources for the RunCommand pod. 
Consider adjusting AutoScaler settings or manually scaling the cluster.
```

**Root Cause**: Your AKS cluster doesn't have enough available resources to schedule the temporary kubectl pod.

### Solutions for Resource-Constrained Clusters

#### Option 1: Enable/Configure Cluster Autoscaling (Recommended)
```bash
# Check current autoscaling configuration
az aks nodepool list --resource-group {resource-group} --cluster-name {cluster-name} \
  --query "[].{name:name,count:count,minCount:minCount,maxCount:maxCount,autoscaling:enableAutoScaling}"

# Enable autoscaling on existing nodepool
az aks nodepool update \
  --resource-group {resource-group} \
  --cluster-name {cluster-name} \
  --name {nodepool-name} \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5

# Update existing autoscaler limits
az aks nodepool update \
  --resource-group {resource-group} \
  --cluster-name {cluster-name} \
  --name {nodepool-name} \
  --update-cluster-autoscaler \
  --min-count 2 \
  --max-count 10
```

#### Option 2: Manual Scaling
```bash
# Scale up nodes temporarily
az aks nodepool scale \
  --resource-group {resource-group} \
  --cluster-name {cluster-name} \
  --name {nodepool-name} \
  --node-count 3

# Scale back down after analysis
az aks nodepool scale \
  --resource-group {resource-group} \
  --cluster-name {cluster-name} \
  --name {nodepool-name} \
  --node-count 1
```

#### Option 3: Add Spot Node Pool (Cost-Effective)
```bash
# Create spot nodepool for temporary workloads
az aks nodepool add \
  --resource-group {resource-group} \
  --cluster-name {cluster-name} \
  --name spot \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --enable-cluster-autoscaler \
  --min-count 0 \
  --max-count 3 \
  --node-vm-size Standard_B2s
```

#### Option 4: Dedicated Nodepool for System Workloads
```bash
# Create dedicated nodepool for system pods and runCommand operations
az aks nodepool add \
  --resource-group {resource-group} \
  --cluster-name {cluster-name} \
  --name system \
  --mode System \
  --node-count 1 \
  --node-vm-size Standard_B2s \
  --node-taints CriticalAddonsOnly=true:NoSchedule
```

### Best Practices for Production Clusters

1. **Always enable autoscaling** with appropriate min/max limits
2. **Monitor resource usage** before running cost analysis
3. **Use spot instances** for temporary analysis workloads
4. **Consider analysis timing** during low-traffic periods
5. **Implement resource quotas** to prevent resource exhaustion

### Monitoring Resource Availability

```bash
# Check node resource usage
kubectl top nodes

# Check pod resource requests/limits
kubectl describe nodes

# Monitor cluster autoscaler events
kubectl get events --field-selector reason=TriggeredScaleUp
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Failures
```
Error: Azure authentication failed
```
**Solutions:**
- Verify service principal credentials are correct
- Check if client secret has expired
- Ensure tenant ID is correct
- Verify service principal is not disabled

#### 2. Subscription Access Denied
```
Error: No access to subscription
```
**Solutions:**
- Verify Reader role is assigned to subscription
- Check if subscription ID is correct
- Ensure service principal has necessary permissions

#### 3. AKS Cluster Access Issues
```
Error: Cannot access AKS cluster
```
**Solutions:**
- Verify "Azure Kubernetes Service RBAC Reader" role
- Check if cluster exists and is running
- Ensure network access to cluster
- Verify resource group permissions

#### 4. Kubernetes RBAC Permission Issues
```
Error: nodes is forbidden: User "service-principal-id" cannot list resource "nodes" 
in API group "" at the cluster scope: User does not have access to the resource in Azure
```
**Root Cause:** Your AKS cluster has Azure RBAC integration enabled, but the service principal lacks Kubernetes-level permissions.

**Solution:**
```bash
# Check if cluster has Azure RBAC integration enabled
az aks show --resource-group {resource-group} --name {cluster-name} \
  --query "aadProfile.enableAzureRbac"

# If true, grant Kubernetes permissions via Azure RBAC
az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service RBAC Cluster Admin" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.ContainerService/managedClusters/{cluster-name}"
```

**Alternative Kubernetes Permission Levels:**
- **Azure Kubernetes Service RBAC Cluster Admin** - Full cluster access (recommended for cost analysis)
- **Azure Kubernetes Service RBAC Admin** - Namespace-level admin access  
- **Azure Kubernetes Service RBAC Reader** - Read-only cluster access
- **Azure Kubernetes Service RBAC Writer** - Read/write access to most resources

#### 5. Cost Data Access Issues
```
Error: Cannot retrieve cost data
```
**Solutions:**
- Verify "Cost Management Reader" role
- Check if subscription has cost data available
- Ensure billing period is valid

### Validation Commands

```bash
# Check service principal permissions
az role assignment list --assignee {service-principal-id} --output table

# Verify subscription access
az account list --all --output table

# Test resource group access
az group list --output table

# Check AKS cluster permissions
az aks list --output table
```

### Debug Mode
Enable debug logging in AKS Cost Optimizer:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Check logs for detailed authentication flow
tail -f logs/app.log | grep -i azure
```

## Security Best Practices

1. **Principle of Least Privilege**
   - Only assign minimum required permissions
   - Use resource-specific scopes when possible

2. **Secret Management**
   - Rotate client secrets regularly (recommended: every 6 months)
   - Store secrets securely (Azure Key Vault recommended)
   - Never commit secrets to source control

3. **Monitoring**
   - Monitor service principal usage via Azure AD audit logs
   - Set up alerts for authentication failures
   - Review permissions quarterly

4. **Network Security**
   - Restrict service principal access to specific IP ranges if possible
   - Use private endpoints for sensitive resources

## OIDC Workload Identity Authentication (Modern Alternative)

### Overview

Azure Workload Identity provides a more secure, credential-free authentication method using OpenID Connect (OIDC) federation. This eliminates the need to store and manage service principal secrets in your KubeOpt application.

### How OIDC Workload Identity Works

```
┌─────────────────┐    OIDC Token     ┌─────────────────┐    Azure AD    ┌─────────────────┐
│  KubeOpt Pod    │ ──────────────── │ AKS OIDC Issuer │ ────────────── │ Managed Identity│
│                 │                  │                 │                │                 │
└─────────────────┘                  └─────────────────┘                └─────────────────┘
        │                                     │                                     │
        │ ServiceAccount                      │ Validates Token                     │ Access to Azure
        │ with annotations                    │ & Issues AAD Token                  │ Resources
        │                                     │                                     │
```

### Benefits Over Service Principal

**✅ Enhanced Security:**
- No secrets to manage or rotate
- Short-lived tokens (1 hour default)
- Automatic token refresh
- No credential storage in cluster

**✅ Simplified Management:**
- No client secret expiration concerns
- Azure-managed authentication flow
- Built-in with AKS (no additional infrastructure)

**✅ Compliance & Audit:**
- Better audit trail through Azure AD
- No secrets in logs or environment variables
- Meets zero-trust security requirements

### Setup Instructions

#### 1. Enable OIDC and Workload Identity on AKS

**For New Clusters:**
```bash
az aks create \
  --resource-group "rg-kubeopt-aks-weu" \
  --name "aks-kubeopt-weu" \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --generate-ssh-keys
```

**For Existing Clusters:**
```bash
# Update existing cluster
az aks update \
  --resource-group "rg-kubeopt-aks-weu" \
  --name "aks-kubeopt-weu" \
  --enable-oidc-issuer \
  --enable-workload-identity
```

#### 2. Create User-Assigned Managed Identity

```bash
# Create managed identity
az identity create \
  --name "kubeopt-workload-identity" \
  --resource-group "rg-kubeopt-aks-weu" \
  --location westeurope

# Get client ID
CLIENT_ID=$(az identity show \
  --resource-group "rg-kubeopt-aks-weu" \
  --name "kubeopt-workload-identity" \
  --query 'clientId' -o tsv)
```

#### 3. Assign Azure RBAC Permissions

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Assign required roles to managed identity
az role assignment create \
  --assignee $CLIENT_ID \
  --role "Reader" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

az role assignment create \
  --assignee $CLIENT_ID \
  --role "Azure Kubernetes Service RBAC Reader" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

az role assignment create \
  --assignee $CLIENT_ID \
  --role "Cost Management Reader" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"
```

#### 4. Create Federated Identity Credential

```bash
# Get AKS OIDC issuer URL
AKS_OIDC_ISSUER=$(az aks show \
  --resource-group "rg-kubeopt-aks-weu" \
  --name "aks-kubeopt-weu" \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Create federated credential
az identity federated-credential create \
  --name "kubeopt-federated-identity" \
  --identity-name "kubeopt-workload-identity" \
  --resource-group "rg-kubeopt-aks-weu" \
  --issuer "$AKS_OIDC_ISSUER" \
  --subject "system:serviceaccount:default:kubeopt-workload-identity" \
  --audience api://AzureADTokenExchange
```

#### 5. Deploy Kubernetes Resources

**ServiceAccount with Workload Identity:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubeopt-workload-identity
  namespace: default
  annotations:
    azure.workload.identity/client-id: "CLIENT_ID_HERE"
```

**Pod with Workload Identity:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubeopt-analyzer
spec:
  template:
    metadata:
      labels:
        azure.workload.identity/use: "true"  # Required label
    spec:
      serviceAccountName: kubeopt-workload-identity
      containers:
      - name: kubeopt
        image: your-kubeopt-image
        env:
        - name: AZURE_CLIENT_ID  # Auto-injected by webhook
        - name: AZURE_TENANT_ID  # Auto-injected by webhook
```

#### 6. Application Configuration

**Update KubeOpt Configuration:**
```python
# In your KubeOpt application, use DefaultAzureCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerservice import ContainerServiceClient

# This automatically uses workload identity when running in AKS
credential = DefaultAzureCredential()
client = ContainerServiceClient(credential, subscription_id)
```

### Multi-Subscription Setup with OIDC

For organizations with multiple subscriptions, create one managed identity per subscription or use cross-subscription access:

```bash
#!/bin/bash
# setup-workload-identity-multi-sub.sh

MANAGED_IDENTITY_NAME="kubeopt-workload-identity"
RESOURCE_GROUP="rg-kubeopt-aks-weu"
SUBSCRIPTIONS=(
    "subscription-id-1"
    "subscription-id-2"
    "subscription-id-3"
)

for SUB_ID in "${SUBSCRIPTIONS[@]}"; do
    echo "Configuring subscription: $SUB_ID"
    az account set --subscription $SUB_ID
    
    # Get managed identity client ID
    CLIENT_ID=$(az identity show \
        --resource-group $RESOURCE_GROUP \
        --name $MANAGED_IDENTITY_NAME \
        --query 'clientId' -o tsv)
    
    # Assign permissions
    az role assignment create --assignee $CLIENT_ID --role "Reader" --scope "/subscriptions/$SUB_ID"
    az role assignment create --assignee $CLIENT_ID --role "Azure Kubernetes Service RBAC Reader" --scope "/subscriptions/$SUB_ID"
    az role assignment create --assignee $CLIENT_ID --role "Cost Management Reader" --scope "/subscriptions/$SUB_ID"
done
```

### Migration from Service Principal to OIDC

**Step 1: Parallel Setup**
- Deploy workload identity alongside existing service principal
- Test authentication and permissions
- Verify all functionality works

**Step 2: Update Application Code**
```python
# Before (Service Principal)
from azure.identity import ClientSecretCredential
credential = ClientSecretCredential(tenant_id, client_id, client_secret)

# After (Workload Identity)
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()  # Automatically uses workload identity
```

**Step 3: Remove Service Principal**
- Delete client secrets
- Remove service principal role assignments
- Clean up environment variables

### Troubleshooting OIDC Workload Identity

#### Common Issues:

**1. Token Exchange Failures:**
```bash
# Check federated credential configuration
az identity federated-credential list \
  --identity-name "kubeopt-workload-identity" \
  --resource-group "rg-kubeopt-aks-weu"
```

**2. ServiceAccount Token Issues:**
```bash
# Verify ServiceAccount annotation
kubectl describe serviceaccount kubeopt-workload-identity

# Check if webhook is injecting environment variables
kubectl describe pod <kubeopt-pod-name>
```

**3. RBAC Permission Issues:**
```bash
# Test managed identity permissions
az role assignment list --assignee $CLIENT_ID --output table
```

### Performance and Limitations

**Token Refresh:**
- Tokens refresh automatically every 1 hour
- No application restart required
- Built-in retry mechanisms

**Rate Limits:**
- AAD token endpoint: 10,000 requests/minute per tenant
- OIDC issuer: No published limits (managed by Azure)

### Security Best Practices

1. **Least Privilege Access:** Only assign minimum required roles
2. **Subject Validation:** Use specific ServiceAccount subjects, not wildcards
3. **Audit Regularly:** Monitor federated credential usage
4. **Network Security:** Use private endpoints where possible
5. **Token Monitoring:** Set up alerts for authentication failures

### Automation Script

Use the provided automation script at `/Users/srini/coderepos/nivaya/kubeopt-aks-infra/azure/enable-workload-identity.sh` to set up workload identity:

```bash
# Make script executable
chmod +x azure/enable-workload-identity.sh

# Run setup
./azure/enable-workload-identity.sh
```

This script will:
- Enable OIDC and workload identity on your AKS cluster
- Create managed identity with proper permissions  
- Set up federated credentials
- Provide next steps for Kubernetes deployment

## Additional Resources

- [Azure Service Principal Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [Azure RBAC Documentation](https://docs.microsoft.com/en-us/azure/role-based-access-control/)
- [AKS RBAC Integration](https://docs.microsoft.com/en-us/azure/aks/azure-ad-rbac)
- [Azure Cost Management API](https://docs.microsoft.com/en-us/rest/api/cost-management/)
- [Azure Workload Identity Documentation](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [OIDC Federation Best Practices](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster)

---

**Note**: This setup provides organization-wide access to AKS clusters and cost data. OIDC Workload Identity is the recommended modern approach for secure, credential-free authentication. Adjust permissions based on your security requirements and organizational policies.