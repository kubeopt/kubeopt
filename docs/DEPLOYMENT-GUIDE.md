# AKS Cost Optimizer - Deployment Guide

**Version:** 1.0  
**Target Environments:** Development, Staging, Production  
**Deployment Methods:** Docker, Kubernetes, Bare Metal  

---

## 📋 **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Security Models](#security-models)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Deployment](#production-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)
10. [Scaling Considerations](#scaling-considerations)

---

## 🔧 **Prerequisites**

### **System Requirements**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **Memory** | 4 GB | 8+ GB |
| **Storage** | 20 GB | 50+ GB SSD |
| **Network** | 1 Gbps | 10+ Gbps |

### **Software Dependencies**

```bash
# Required Software
- Docker 20.10+
- Docker Compose 2.0+
- Azure CLI 2.50+
- Python 3.11+ (for development)
- Git (for source code)

# Optional (for Kubernetes deployment)
- kubectl 1.25+
- Helm 3.10+
- Terraform 1.5+ (for infrastructure)
```

### **Azure Prerequisites**

#### **Azure Permissions Required**
```json
{
  "required_permissions": [
    "Microsoft.ContainerService/managedClusters/read",
    "Microsoft.CostManagement/query/action",
    "Microsoft.Insights/metrics/read", 
    "Microsoft.Resources/subscriptions/read",
    "Microsoft.Authorization/roleAssignments/read",
    "Microsoft.Monitor/logAnalytics/workspaces/read",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Network/networkInterfaces/read",
    "Microsoft.Storage/storageAccounts/read"
  ]
}
```

#### **Azure Service Principal Setup**
```bash
# Create service principal
az ad sp create-for-rbac \
  --name "aks-cost-optimizer" \
  --role "Cost Management Reader" \
  --scopes "/subscriptions/{subscription-id}"

# Add additional roles
az role assignment create \
  --assignee {service-principal-id} \
  --role "Monitoring Reader" \
  --scope "/subscriptions/{subscription-id}"

az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service Cluster User Role" \
  --scope "/subscriptions/{subscription-id}"
```

---

## 🔒 **Security Models**

### **Security Model Comparison**

| Model | Security Level | Use Case | Performance Impact |
|-------|---------------|----------|-------------------|
| **PyInstaller** | ⭐⭐⭐⭐⭐ | Production | Low |
| **Bytecode** | ⭐⭐⭐⭐ | Staging | Very Low |
| **Obfuscated** | ⭐⭐⭐⭐⭐ | High Security | Low |
| **Source** | ⭐⭐ | Development | None |

### **Security Model Details**

#### **1. PyInstaller Model (Default/Recommended)**
```dockerfile
# Dockerfile (default)
FROM python:3.11-slim-bookworm AS builder
# Compiles Python code to standalone executable
# No source code in final container
# Best security vs performance balance
```

**Features:**
- ✅ Source code compiled to binary
- ✅ No Python interpreter in runtime
- ✅ Minimal attack surface
- ✅ Fast startup time

#### **2. Bytecode Compilation Model**
```dockerfile
# Dockerfile.bytecode
FROM python:3.11-slim-bookworm
# Compiles Python to bytecode (.pyc files)
# Removes source code (.py files)
# Good security with python runtime
```

**Features:**
- ✅ Source code compiled to bytecode
- ✅ Python interpreter available for debugging
- ✅ Good performance
- ⚠️ Bytecode can be decompiled

#### **3. Code Obfuscation Model**
```dockerfile
# Dockerfile.obfuscated
FROM python:3.11-slim-bookworm
# Uses code obfuscation techniques
# Makes reverse engineering very difficult
# Highest security for source-based deployment
```

**Features:**
- ✅ Advanced code obfuscation
- ✅ Multiple obfuscation layers
- ✅ Very difficult to reverse engineer
- ⚠️ Slight performance overhead

---

## 🐳 **Docker Deployment**

### **Quick Start Deployment**

#### **1. Standard Deployment (PyInstaller - Recommended)**
```bash
# Clone repository
git clone <repository-url>
cd aks-cost-optimizer

# Build with default security model
docker build -t aks-cost-optimizer:latest .

# Run with environment variables
docker run -d \
  --name aks-cost-optimizer \
  -p 5000:5000 \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  -e FLASK_ENV=production \
  -e LOG_LEVEL=INFO \
  -v aks_data:/app/infrastructure/persistence/database \
  -v aks_logs:/app/logs \
  --restart unless-stopped \
  aks-cost-optimizer:latest
```

#### **2. Development Deployment**
```bash
# Development with docker-compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f aks-optimizer
```

#### **3. Production Deployment**
```bash
# Production with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# With custom environment file
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### **Multi-Variant Security Deployment**

#### **Build All Security Variants**
```bash
# Build all variants at once
./deploy/docker/build-secure-containers.sh latest all

# Available variants:
# - aks-cost-optimizer:latest-pyinstaller (default)
# - aks-cost-optimizer:latest-bytecode
# - aks-cost-optimizer:latest-obfuscated
```

#### **Deploy Specific Security Model**
```bash
# Deploy PyInstaller variant (most secure)
docker run -d \
  --name aks-optimizer-secure \
  -p 5000:5000 \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  aks-cost-optimizer:latest-pyinstaller

# Deploy with secure compose file
docker-compose -f deploy/docker/docker-compose.secure.yml up -d
```

### **Environment File Configuration**

#### **Create .env.production**
```bash
# Azure Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_CONFIG_DIR=/home/appuser/.azure
AZURE_CORE_COLLECT_TELEMETRY=false

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO
DATABASE_PATH=/app/data/aks_optimizer.db
PYTHONPATH=/app
APP_URL=https://your-domain.com

# Notification Settings (Optional)
EMAIL_ENABLED=true
SMTP_SERVER=smtpout.secureserver.net
SMTP_PORT=587
SMTP_USERNAME=alerts@your-domain.com
SMTP_PASSWORD=your-email-password
EMAIL_RECIPIENTS=admin@your-domain.com,devops@your-domain.com

SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#aks-cost-alerts

# Feature Configuration
ENABLE_MULTI_SUBSCRIPTION=true
PARALLEL_PROCESSING=true
LICENSE_TIER=enterprise

# Performance Tuning
CACHE_TTL_HOURS=1
MAX_ANALYSIS_THREADS=4
BACKGROUND_PROCESSING_ENABLED=true

# Security Settings
SESSION_TIMEOUT_MINUTES=60
MAX_LOGIN_ATTEMPTS=3
REQUIRE_STRONG_PASSWORDS=true
```

---

## ☸️ **Kubernetes Deployment**

### **Namespace Setup**

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aks-cost-optimizer
  labels:
    name: aks-cost-optimizer
    environment: production
```

### **Secret Management**

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: azure-credentials
  namespace: aks-cost-optimizer
type: Opaque
data:
  # Base64 encoded values
  tenant-id: <base64-encoded-tenant-id>
  client-id: <base64-encoded-client-id>
  client-secret: <base64-encoded-client-secret>
  subscription-id: <base64-encoded-subscription-id>
```

```bash
# Create secret from command line
kubectl create secret generic azure-credentials \
  --from-literal=tenant-id=your-tenant-id \
  --from-literal=client-id=your-client-id \
  --from-literal=client-secret=your-client-secret \
  --from-literal=subscription-id=your-subscription-id \
  -n aks-cost-optimizer
```

### **ConfigMap for Application Settings**

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: aks-cost-optimizer
data:
  FLASK_ENV: "production"
  LOG_LEVEL: "INFO"
  ENABLE_MULTI_SUBSCRIPTION: "true"
  PARALLEL_PROCESSING: "true"
  CACHE_TTL_HOURS: "1"
  MAX_ANALYSIS_THREADS: "4"
```

### **Persistent Storage**

```yaml
# storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: aks-optimizer-data
  namespace: aks-cost-optimizer
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: premium-ssd
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: aks-optimizer-logs
  namespace: aks-cost-optimizer
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard-ssd
```

### **Deployment Manifest**

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aks-cost-optimizer
  namespace: aks-cost-optimizer
  labels:
    app: aks-cost-optimizer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aks-cost-optimizer
  template:
    metadata:
      labels:
        app: aks-cost-optimizer
    spec:
      serviceAccountName: aks-cost-optimizer
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: aks-cost-optimizer
        image: aks-cost-optimizer:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: AZURE_TENANT_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: tenant-id
        - name: AZURE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: client-id
        - name: AZURE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: client-secret
        - name: AZURE_SUBSCRIPTION_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: subscription-id
        envFrom:
        - configMapRef:
            name: app-config
        volumeMounts:
        - name: data-volume
          mountPath: /app/infrastructure/persistence/database
        - name: logs-volume
          mountPath: /app/logs
        - name: azure-config
          mountPath: /home/appuser/.azure
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: aks-optimizer-data
      - name: logs-volume
        persistentVolumeClaim:
          claimName: aks-optimizer-logs
      - name: azure-config
        emptyDir: {}
```

### **Service & Ingress**

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: aks-cost-optimizer-service
  namespace: aks-cost-optimizer
spec:
  selector:
    app: aks-cost-optimizer
  ports:
  - name: http
    port: 80
    targetPort: 5000
    protocol: TCP
  type: ClusterIP
---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aks-cost-optimizer-ingress
  namespace: aks-cost-optimizer
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - aks-optimizer.yourdomain.com
    secretName: aks-optimizer-tls
  rules:
  - host: aks-optimizer.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aks-cost-optimizer-service
            port:
              number: 80
```

### **RBAC Configuration**

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aks-cost-optimizer
  namespace: aks-cost-optimizer
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aks-cost-optimizer-role
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "services", "persistentvolumes", "persistentvolumeclaims"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["nodes", "pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: aks-cost-optimizer-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: aks-cost-optimizer-role
subjects:
- kind: ServiceAccount
  name: aks-cost-optimizer
  namespace: aks-cost-optimizer
```

### **Deployment Commands**

```bash
# Deploy to Kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f storage.yaml
kubectl apply -f rbac.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify deployment
kubectl get all -n aks-cost-optimizer
kubectl logs -f deployment/aks-cost-optimizer -n aks-cost-optimizer

# Check ingress
kubectl get ingress -n aks-cost-optimizer
```

---

## 🏭 **Production Deployment**

### **High Availability Setup**

#### **Load Balancer Configuration**
```yaml
# ha-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aks-cost-optimizer
  namespace: aks-cost-optimizer
spec:
  replicas: 3  # High availability
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - aks-cost-optimizer
              topologyKey: kubernetes.io/hostname
```

#### **Horizontal Pod Autoscaler**
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aks-cost-optimizer-hpa
  namespace: aks-cost-optimizer
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aks-cost-optimizer
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **Database High Availability**

#### **External Database Setup**
```yaml
# For production, consider external database
# PostgreSQL or Azure SQL Database
apiVersion: v1
kind: ConfigMap
metadata:
  name: database-config
  namespace: aks-cost-optimizer
data:
  DATABASE_TYPE: "postgresql"
  DATABASE_HOST: "your-postgres-host"
  DATABASE_NAME: "aks_optimizer"
  DATABASE_PORT: "5432"
```

#### **Database Migration Job**
```yaml
# db-migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration
  namespace: aks-cost-optimizer
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: migration
        image: aks-cost-optimizer:latest
        command: ["python", "-m", "infrastructure.persistence.scripts.migrate_database"]
        envFrom:
        - configMapRef:
            name: database-config
        - secretRef:
            name: database-credentials
```

### **Production Environment Variables**

```bash
# .env.production (complete)
# ===========================
# Azure Configuration
# ===========================
AZURE_TENANT_ID=your-production-tenant-id
AZURE_CLIENT_ID=your-production-client-id
AZURE_CLIENT_SECRET=your-production-client-secret
AZURE_SUBSCRIPTION_ID=your-production-subscription-id
AZURE_CONFIG_DIR=/home/appuser/.azure
AZURE_CORE_COLLECT_TELEMETRY=false

# ===========================
# Application Settings
# ===========================
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-super-secure-secret-key
LOG_LEVEL=INFO
PYTHONPATH=/app

# ===========================
# Database Configuration
# ===========================
DATABASE_TYPE=postgresql
DATABASE_HOST=your-postgres-host
DATABASE_NAME=aks_optimizer_prod
DATABASE_USER=aks_optimizer_user
DATABASE_PASSWORD=your-secure-db-password
DATABASE_PORT=5432
DATABASE_SSL_MODE=require

# ===========================
# Feature Configuration
# ===========================
ENABLE_MULTI_SUBSCRIPTION=true
PARALLEL_PROCESSING=true
LICENSE_TIER=enterprise
AUTO_ANALYSIS_ENABLED=true
AUTO_ANALYSIS_INTERVAL=240m

# ===========================
# Performance Tuning
# ===========================
CACHE_TTL_HOURS=1
MAX_ANALYSIS_THREADS=8
BACKGROUND_PROCESSING_ENABLED=true
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000

# ===========================
# Security Settings
# ===========================
SESSION_TIMEOUT_MINUTES=60
MAX_LOGIN_ATTEMPTS=5
REQUIRE_STRONG_PASSWORDS=true
ENABLE_2FA=true
CORS_ORIGINS=https://your-domain.com

# ===========================
# Monitoring & Alerting
# ===========================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
ALERT_EMAIL=admin@yourdomain.com
SLACK_WEBHOOK_URL=your-slack-webhook-url

# ===========================
# External Integrations
# ===========================
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_TLS=true
```

---

## 📊 **Monitoring & Logging**

### **Prometheus Monitoring**

#### **ServiceMonitor for Prometheus**
```yaml
# monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: aks-cost-optimizer-metrics
  namespace: aks-cost-optimizer
spec:
  selector:
    matchLabels:
      app: aks-cost-optimizer
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

#### **Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "AKS Cost Optimizer Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Cost Analysis Count",
        "targets": [
          {
            "expr": "aks_optimizer_analysis_total"
          }
        ]
      }
    ]
  }
}
```

### **Centralized Logging**

#### **Fluentd Configuration**
```yaml
# fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: aks-cost-optimizer
data:
  fluent.conf: |
    <source>
      @type tail
      path /app/logs/*.log
      pos_file /var/log/fluentd-aks-optimizer.log.pos
      tag aks-optimizer.*
      format json
    </source>
    
    <match aks-optimizer.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name aks-optimizer
      type_name logs
    </match>
```

### **Alerting Rules**

#### **PrometheusRule for Alerts**
```yaml
# alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: aks-cost-optimizer-alerts
  namespace: aks-cost-optimizer
spec:
  groups:
  - name: aks-cost-optimizer
    rules:
    - alert: HighErrorRate
      expr: rate(flask_http_request_exceptions_total[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate in AKS Cost Optimizer"
        
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes{pod=~"aks-cost-optimizer.*"} / container_spec_memory_limit_bytes > 0.9
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "High memory usage in AKS Cost Optimizer"
        
    - alert: ServiceDown
      expr: up{job="aks-cost-optimizer"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "AKS Cost Optimizer service is down"
```

---

## 💾 **Backup & Recovery**

### **Database Backup Strategy**

#### **Automated Backup CronJob**
```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: aks-cost-optimizer
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME > /backup/aks_optimizer_$(date +%Y%m%d_%H%M%S).sql
              # Upload to Azure Blob Storage
              az storage blob upload \
                --file /backup/aks_optimizer_$(date +%Y%m%d_%H%M%S).sql \
                --container-name backups \
                --name aks_optimizer_$(date +%Y%m%d_%H%M%S).sql
            env:
            - name: DATABASE_HOST
              valueFrom:
                configMapKeyRef:
                  name: database-config
                  key: DATABASE_HOST
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-storage
```

### **Recovery Procedures**

#### **Database Recovery Script**
```bash
#!/bin/bash
# recovery.sh

set -e

BACKUP_FILE=$1
DATABASE_HOST=$2
DATABASE_NAME=$3
DATABASE_USER=$4

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file> [database_host] [database_name] [database_user]"
    exit 1
fi

# Default values
DATABASE_HOST=${DATABASE_HOST:-localhost}
DATABASE_NAME=${DATABASE_NAME:-aks_optimizer}
DATABASE_USER=${DATABASE_USER:-aks_optimizer_user}

echo "Starting database recovery..."
echo "Backup file: $BACKUP_FILE"
echo "Database host: $DATABASE_HOST"
echo "Database name: $DATABASE_NAME"

# Download backup from Azure Blob Storage if needed
if [[ $BACKUP_FILE == https://* ]]; then
    echo "Downloading backup from Azure..."
    az storage blob download \
        --container-name backups \
        --name $(basename $BACKUP_FILE) \
        --file /tmp/$(basename $BACKUP_FILE)
    BACKUP_FILE="/tmp/$(basename $BACKUP_FILE)"
fi

# Stop application
kubectl scale deployment aks-cost-optimizer --replicas=0 -n aks-cost-optimizer

# Restore database
echo "Restoring database..."
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME < $BACKUP_FILE

# Start application
kubectl scale deployment aks-cost-optimizer --replicas=2 -n aks-cost-optimizer

echo "Recovery completed successfully!"
```

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

#### **1. Azure Authentication Issues**

**Problem:** `Azure authentication failed`
```bash
# Check Azure credentials
kubectl get secret azure-credentials -n aks-cost-optimizer -o yaml

# Test Azure connection
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  az login --service-principal \
    --username $AZURE_CLIENT_ID \
    --password $AZURE_CLIENT_SECRET \
    --tenant $AZURE_TENANT_ID
```

**Solution:**
```bash
# Update credentials
kubectl delete secret azure-credentials -n aks-cost-optimizer
kubectl create secret generic azure-credentials \
  --from-literal=tenant-id=new-tenant-id \
  --from-literal=client-id=new-client-id \
  --from-literal=client-secret=new-client-secret \
  --from-literal=subscription-id=new-subscription-id \
  -n aks-cost-optimizer

# Restart deployment
kubectl rollout restart deployment/aks-cost-optimizer -n aks-cost-optimizer
```

#### **2. Database Connection Issues**

**Problem:** `Database connection failed`
```bash
# Check database connectivity
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  python -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/infrastructure/persistence/database/clusters.db')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

**Solution:**
```bash
# Check storage permissions
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  ls -la /app/infrastructure/persistence/database/

# Fix permissions if needed
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  chown -R 1000:1000 /app/infrastructure/persistence/database/
```

#### **3. Memory Issues**

**Problem:** `Out of memory errors`
```bash
# Check memory usage
kubectl top pods -n aks-cost-optimizer

# Check memory limits
kubectl describe pod <pod-name> -n aks-cost-optimizer | grep -A 5 "Limits:"
```

**Solution:**
```yaml
# Increase memory limits
resources:
  requests:
    memory: "4Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi" 
    cpu: "4000m"
```

#### **4. Performance Issues**

**Problem:** `Slow analysis performance`
```bash
# Check CPU usage
kubectl top pods -n aks-cost-optimizer

# Check analysis queue
kubectl logs deployment/aks-cost-optimizer -n aks-cost-optimizer | grep "analysis_queue"
```

**Solution:**
```bash
# Scale up deployment
kubectl scale deployment aks-cost-optimizer --replicas=5 -n aks-cost-optimizer

# Or update resources
kubectl patch deployment aks-cost-optimizer -n aks-cost-optimizer -p='
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "aks-cost-optimizer",
          "resources": {
            "requests": {"cpu": "2000m", "memory": "4Gi"},
            "limits": {"cpu": "4000m", "memory": "8Gi"}
          }
        }]
      }
    }
  }
}'
```

### **Diagnostic Commands**

```bash
# Complete health check
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  curl -f http://localhost:5000/health/detailed

# Check application logs
kubectl logs deployment/aks-cost-optimizer -n aks-cost-optimizer --tail=100

# Check Azure SDK status
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  python -c "
from infrastructure.services.azure_sdk_manager import AzureSDKManager
manager = AzureSDKManager()
status = manager.test_connection()
print(f'Azure connection status: {status}')
"

# Database diagnostics
kubectl exec -it deployment/aks-cost-optimizer -n aks-cost-optimizer -- \
  python -m infrastructure.persistence.scripts.diagnosys
```

---

## 📈 **Scaling Considerations**

### **Vertical Scaling**

#### **Resource Optimization**
```yaml
# High-performance configuration
resources:
  requests:
    memory: "8Gi"
    cpu: "4000m"
  limits:
    memory: "16Gi"
    cpu: "8000m"

# Environment variables for performance
env:
- name: MAX_ANALYSIS_THREADS
  value: "16"
- name: WORKER_PROCESSES
  value: "8"
- name: CACHE_TTL_HOURS
  value: "0.5"  # More aggressive caching
```

### **Horizontal Scaling**

#### **Multi-Region Deployment**
```yaml
# Regional deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aks-cost-optimizer-us-east
  namespace: aks-cost-optimizer
spec:
  replicas: 3
  template:
    spec:
      nodeSelector:
        topology.kubernetes.io/region: us-east-1
      tolerations:
      - key: region
        operator: Equal
        value: us-east-1
        effect: NoSchedule
```

#### **Database Sharding Strategy**
```python
# Multi-subscription database sharding
SUBSCRIPTION_SHARD_CONFIG = {
    'shard_1': {
        'subscriptions': ['subscription-1', 'subscription-2'],
        'database_host': 'postgres-shard-1.example.com'
    },
    'shard_2': {
        'subscriptions': ['subscription-3', 'subscription-4'],
        'database_host': 'postgres-shard-2.example.com'
    }
}
```

### **Performance Benchmarks**

| Configuration | Clusters/Hour | Memory Usage | CPU Usage |
|---------------|---------------|--------------|-----------|
| **Minimal** (2 CPU, 4GB) | 50 | 2.5GB | 70% |
| **Standard** (4 CPU, 8GB) | 150 | 5.2GB | 60% |
| **High-Performance** (8 CPU, 16GB) | 400 | 10.1GB | 65% |
| **Enterprise** (16 CPU, 32GB) | 1000+ | 18.5GB | 70% |

---

## 🔐 **Security Hardening**

### **Network Security**

#### **Network Policies**
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aks-cost-optimizer-netpol
  namespace: aks-cost-optimizer
spec:
  podSelector:
    matchLabels:
      app: aks-cost-optimizer
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to: []  # Allow all outbound (Azure APIs)
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

### **Pod Security Standards**

#### **Pod Security Policy**
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: aks-cost-optimizer-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  runAsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 1000
  fsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 1000
```

---

This comprehensive deployment guide provides everything needed to deploy the AKS Cost Optimizer in various environments with proper security, monitoring, and scaling considerations. Choose the appropriate deployment method based on your specific requirements and environment constraints.