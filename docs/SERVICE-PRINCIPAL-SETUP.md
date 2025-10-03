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

#### 1. Subscription-Level Permissions
Apply these roles to **all subscriptions** containing AKS clusters:

```bash
# Replace {service-principal-id} with your service principal's appId
# Replace {subscription-id} with each subscription ID

# Basic read access to resources
az role assignment create \
  --assignee {service-principal-id} \
  --role "Reader" \
  --scope "/subscriptions/{subscription-id}"

# Cost management access
az role assignment create \
  --assignee {service-principal-id} \
  --role "Cost Management Reader" \
  --scope "/subscriptions/{subscription-id}"

# Monitor and metrics access
az role assignment create \
  --assignee {service-principal-id} \
  --role "Monitoring Reader" \
  --scope "/subscriptions/{subscription-id}"

# AKS cluster metadata access (REQUIRED for cluster operations)
az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service RBAC Reader" \
  --scope "/subscriptions/{subscription-id}"
```

#### 2. AKS-Specific Permissions
For each AKS cluster or resource group:

```bash
# STEP 1: Create custom role for kubectl runCommand operations (REQUIRED)
# Based on latest Azure documentation (2024-2025), built-in roles do NOT include runCommand permissions
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

# STEP 2: Assign the custom runCommand role to your cluster
az role assignment create \
  --assignee {service-principal-id} \
  --role "AKS Run Command Role" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.ContainerService/managedClusters/{cluster-name}"

# STEP 3: Also assign cluster user role for additional AKS operations
az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service Cluster User Role" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.ContainerService/managedClusters/{cluster-name}"

# STEP 4: Grant Kubernetes RBAC permissions (REQUIRED for kubectl operations inside cluster)
# This is needed for clusters with Azure RBAC integration enabled
az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service RBAC Cluster Admin" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.ContainerService/managedClusters/{cluster-name}"

# Alternative: Apply to entire resource group (recommended for multiple clusters)
az role assignment create \
  --assignee {service-principal-id} \
  --role "AKS Run Command Role" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"

az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service Cluster User Role" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"

az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service RBAC Cluster Admin" \
  --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"
```

**⚠️ IMPORTANT NOTES**: 
1. The `runCommand` permissions are NOT included in any built-in Azure roles as of 2024-2025. The custom role above is **REQUIRED** for kubectl operations to work through Azure's runCommand API.
2. The runCommand feature creates temporary pods with resource requirements (200m CPU, 500Mi memory requests). See [Resource Requirements](#runcommand-resource-requirements) section below.
3. **Azure Kubernetes Service RBAC Cluster Admin** is REQUIRED for clusters with Azure RBAC integration enabled. This grants Kubernetes cluster-admin permissions through Azure RBAC instead of traditional Kubernetes RBAC.

#### 3. Management Group Level (Enterprise Setup)
For organization-wide access across all subscriptions:

```bash
# Apply Reader role at Management Group level
az role assignment create \
  --assignee {service-principal-id} \
  --role "Reader" \
  --scope "/providers/Microsoft.Management/managementGroups/{management-group-id}"

# Apply Cost Management Reader at Management Group level
az role assignment create \
  --assignee {service-principal-id} \
  --role "Cost Management Reader" \
  --scope "/providers/Microsoft.Management/managementGroups/{management-group-id}"
```

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

## Additional Resources

- [Azure Service Principal Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [Azure RBAC Documentation](https://docs.microsoft.com/en-us/azure/role-based-access-control/)
- [AKS RBAC Integration](https://docs.microsoft.com/en-us/azure/aks/azure-ad-rbac)
- [Azure Cost Management API](https://docs.microsoft.com/en-us/rest/api/cost-management/)

---

**Note**: This setup provides organization-wide access to AKS clusters and cost data. Adjust permissions based on your security requirements and organizational policies.