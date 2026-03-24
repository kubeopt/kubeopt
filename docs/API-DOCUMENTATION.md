# KubeOpt - API Documentation

**Version:** 2.0
**Base URL:** `http://localhost:5001` (development) | `https://your-domain.com` (production)
**Authentication:** JWT Bearer Token

---

## 📋 **Table of Contents**

1. [Authentication](#authentication)
2. [Core Analysis APIs](#core-analysis-apis)
3. [Cost Optimization APIs](#cost-optimization-apis)
4. [Machine Learning APIs](#machine-learning-apis)
5. [Security Analysis APIs](#security-analysis-apis)
6. [Enterprise Management APIs](#enterprise-management-apis)
7. [Configuration APIs](#configuration-apis)
8. [Health & Monitoring APIs](#health--monitoring-apis)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## 🔐 **Authentication**

### **Session-based Authentication (Web Interface)**
```bash
# Login
POST /auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}

# Response
{
  "success": true,
  "message": "Login successful",
  "user": {
    "username": "your-username",
    "tier": "enterprise",
    "permissions": ["cost_analysis", "ml_insights", "security_analysis"]
  }
}
```

### **API Token Authentication (Programmatic Access)**
```bash
# All API requests require Authorization header
Authorization: Bearer your-api-token

# Or session cookie (for web interface)
Cookie: session=your-session-id
```

---

## 📊 **Core Analysis APIs**

### **1. Cluster Analysis**

#### **Analyze Specific Cluster**
```bash
GET /api/analyze/cluster/{cluster_name}
```

**Parameters:**
- `cluster_name` (path): Name of the AKS cluster
- `subscription_id` (query, optional): Azure subscription ID
- `resource_group` (query, optional): Resource group name

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "subscription_id": "abc-123-def",
  "analysis_timestamp": "2025-09-30T10:30:00Z",
  "cluster_info": {
    "node_count": 3,
    "node_size": "Standard_D2s_v3",
    "kubernetes_version": "1.28.0",
    "location": "eastus"
  },
  "cost_analysis": {
    "monthly_cost": 1250.00,
    "cost_breakdown": {
      "compute": 800.00,
      "storage": 250.00,
      "networking": 150.00,
      "control_plane": 50.00
    }
  },
  "utilization": {
    "cpu_utilization": 35.5,
    "memory_utilization": 42.3,
    "storage_utilization": 67.8
  },
  "optimization_opportunities": {
    "potential_savings": 375.00,
    "savings_percentage": 30.0,
    "recommendations_count": 8
  }
}
```

#### **Get All Clusters**
```bash
GET /api/clusters
```

**Query Parameters:**
- `subscription_id` (optional): Filter by subscription
- `status` (optional): Filter by status (active, inactive, error)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "clusters": [
    {
      "cluster_name": "cluster-1",
      "subscription_id": "abc-123-def",
      "resource_group": "rg-aks-prod",
      "status": "active",
      "last_analyzed": "2025-09-30T10:30:00Z",
      "monthly_cost": 1250.00,
      "potential_savings": 375.00
    }
  ],
  "total_count": 15,
  "pagination": {
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

### **2. Real-time Metrics**

#### **Get Real-time Cluster Metrics**
```bash
GET /api/metrics/realtime/{cluster_name}
```

**Query Parameters:**
- `timeframe` (optional): 1h, 6h, 24h, 7d (default: 1h)
- `metrics` (optional): cpu,memory,storage,network (default: all)

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "timeframe": "1h",
  "metrics": {
    "cpu": {
      "current": 35.5,
      "average": 32.1,
      "peak": 67.8,
      "trend": "stable"
    },
    "memory": {
      "current": 42.3,
      "average": 39.7,
      "peak": 78.2,
      "trend": "increasing"
    },
    "nodes": [
      {
        "name": "aks-nodepool1-12345678-vmss000000",
        "cpu_percent": 28.5,
        "memory_percent": 35.2,
        "disk_percent": 45.7
      }
    ]
  },
  "timestamp": "2025-09-30T10:30:00Z"
}
```

---

## 💰 **Cost Optimization APIs**

### **1. Cost Analysis**

#### **Get Cost Breakdown**
```bash
GET /api/cost/breakdown/{cluster_name}
```

**Query Parameters:**
- `period` (optional): daily, weekly, monthly (default: monthly)
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "period": "monthly",
  "total_cost": 1250.00,
  "cost_breakdown": {
    "compute": {
      "amount": 800.00,
      "percentage": 64.0,
      "details": {
        "node_pools": [
          {
            "name": "nodepool1",
            "instance_type": "Standard_D2s_v3",
            "instance_count": 3,
            "monthly_cost": 450.00
          }
        ]
      }
    },
    "storage": {
      "amount": 250.00,
      "percentage": 20.0,
      "details": {
        "premium_ssd": 180.00,
        "standard_ssd": 70.00
      }
    },
    "networking": {
      "amount": 150.00,
      "percentage": 12.0,
      "details": {
        "load_balancer": 80.00,
        "public_ip": 30.00,
        "data_transfer": 40.00
      }
    },
    "control_plane": {
      "amount": 50.00,
      "percentage": 4.0
    }
  },
  "historical_trend": [
    {
      "date": "2025-09-01",
      "cost": 1180.00
    },
    {
      "date": "2025-09-15",
      "cost": 1215.00
    },
    {
      "date": "2025-09-30",
      "cost": 1250.00
    }
  ]
}
```

### **2. Optimization Recommendations**

#### **Get Optimization Recommendations**
```bash
GET /api/optimize/recommendations/{cluster_name}
```

**Query Parameters:**
- `category` (optional): cost, performance, security (default: all)
- `priority` (optional): high, medium, low (default: all)
- `savings_threshold` (optional): Minimum savings amount (default: 0)

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "total_recommendations": 8,
  "potential_total_savings": 375.00,
  "recommendations": [
    {
      "id": "rec-001",
      "category": "cost",
      "priority": "high",
      "title": "Right-size over-provisioned nodes",
      "description": "Nodes are running at 35% CPU utilization. Consider scaling down or using smaller instance types.",
      "potential_savings": 200.00,
      "savings_percentage": 25.0,
      "implementation_effort": "medium",
      "risk_level": "low",
      "implementation_plan": {
        "steps": [
          "1. Monitor workload patterns for 24 hours",
          "2. Create test environment with smaller instances",
          "3. Gradually migrate workloads",
          "4. Monitor performance metrics"
        ],
        "estimated_time": "2-4 hours",
        "rollback_plan": "Scale back to original instance sizes if performance degrades"
      }
    },
    {
      "id": "rec-002", 
      "category": "cost",
      "priority": "medium",
      "title": "Optimize storage tiers",
      "description": "Some persistent volumes are using Premium SSD for non-critical workloads.",
      "potential_savings": 90.00,
      "savings_percentage": 36.0,
      "implementation_effort": "low",
      "risk_level": "low",
      "affected_resources": [
        "pvc-web-app-data",
        "pvc-cache-storage"
      ]
    }
  ]
}
```

### **3. Implementation Planning**

#### **Generate Implementation Plan**
```bash
POST /api/generate/implementation-plan
Content-Type: application/json

{
  "cluster_name": "my-aks-cluster",
  "optimization_level": "aggressive",
  "selected_recommendations": ["rec-001", "rec-002"],
  "timeline_preference": "gradual",
  "risk_tolerance": "medium"
}
```

**Response:**
```json
{
  "plan_id": "plan-abc123",
  "cluster_name": "my-aks-cluster",
  "total_estimated_savings": 290.00,
  "implementation_phases": [
    {
      "phase": 1,
      "title": "Low-Risk Quick Wins",
      "duration": "1-2 days",
      "recommendations": ["rec-002"],
      "estimated_savings": 90.00,
      "risk_level": "low",
      "tasks": [
        {
          "task": "Backup current PVC configurations",
          "estimated_time": "30 minutes",
          "dependencies": []
        },
        {
          "task": "Update storage classes for non-critical volumes",
          "estimated_time": "1 hour",
          "dependencies": ["backup_configs"]
        }
      ]
    },
    {
      "phase": 2,
      "title": "Infrastructure Optimization",
      "duration": "3-5 days",
      "recommendations": ["rec-001"],
      "estimated_savings": 200.00,
      "risk_level": "medium",
      "prerequisites": [
        "Phase 1 completion",
        "24-hour monitoring period"
      ]
    }
  ],
  "monitoring_plan": {
    "metrics_to_track": ["cpu_utilization", "memory_utilization", "response_time"],
    "alert_thresholds": {
      "cpu_utilization": 80,
      "memory_utilization": 85,
      "response_time_95th_percentile": 2000
    }
  },
  "rollback_procedures": [
    {
      "trigger": "CPU utilization > 85% for 10 minutes",
      "action": "Scale back to original instance sizes",
      "estimated_time": "15 minutes"
    }
  ]
}
```

---

## 🤖 **Machine Learning APIs**

### **1. Anomaly Detection**

#### **Detect Cost Anomalies**
```bash
GET /api/ml/anomalies/{cluster_name}
```

**Query Parameters:**
- `timeframe` (optional): 24h, 7d, 30d (default: 7d)
- `sensitivity` (optional): low, medium, high (default: medium)

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "analysis_period": "7d",
  "anomalies_detected": 3,
  "anomalies": [
    {
      "id": "anomaly-001",
      "timestamp": "2025-09-28T14:30:00Z",
      "severity": "high",
      "type": "cost_spike",
      "description": "Unexpected 45% cost increase in compute resources",
      "detected_value": 580.00,
      "expected_range": [320.00, 400.00],
      "confidence_score": 0.92,
      "possible_causes": [
        "Auto-scaling triggered by increased load",
        "New workload deployment",
        "Resource misconfiguration"
      ],
      "recommended_actions": [
        "Review recent deployments",
        "Check HPA configuration",
        "Analyze workload patterns"
      ]
    }
  ],
  "trend_analysis": {
    "cost_trend": "increasing",
    "predicted_monthly_cost": 1450.00,
    "confidence_interval": [1380.00, 1520.00]
  }
}
```

### **2. Performance Predictions**

#### **Get Performance Predictions**
```bash
GET /api/ml/predictions/{cluster_name}
```

**Query Parameters:**
- `prediction_horizon` (optional): 1d, 7d, 30d (default: 7d)
- `metrics` (optional): cost, cpu, memory, storage (default: all)

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "prediction_horizon": "7d",
  "predictions": {
    "cost": {
      "current_weekly": 290.00,
      "predicted_weekly": 315.00,
      "confidence": 0.87,
      "trend": "increasing",
      "factors": [
        "Seasonal traffic increase expected",
        "New feature rollout planned"
      ]
    },
    "resource_utilization": {
      "cpu": {
        "current_avg": 35.5,
        "predicted_avg": 42.3,
        "peak_prediction": 68.7,
        "scaling_recommendation": "Consider adding 1 additional node"
      },
      "memory": {
        "current_avg": 42.3,
        "predicted_avg": 48.9,
        "peak_prediction": 72.1,
        "scaling_recommendation": "Current capacity sufficient"
      }
    }
  },
  "recommendations": [
    "Schedule additional capacity for expected traffic increase",
    "Monitor memory usage closely during peak periods"
  ]
}
```

### **3. Workload Analysis**

#### **Analyze Workload DNA**
```bash
GET /api/ml/workload-analysis/{cluster_name}
```

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "workload_dna": {
    "classification": "web_application",
    "traffic_pattern": "business_hours_peaks",
    "resource_characteristics": {
      "cpu_intensive": false,
      "memory_intensive": true,
      "io_intensive": false,
      "network_intensive": true
    },
    "scaling_behavior": {
      "auto_scaling_efficiency": 0.78,
      "scale_up_speed": "medium",
      "scale_down_speed": "slow",
      "optimal_min_replicas": 2,
      "optimal_max_replicas": 12
    }
  },
  "optimization_insights": [
    "Memory-based HPA would be more effective than CPU-based",
    "Consider implementing predictive scaling for traffic peaks",
    "Network optimization could reduce latency by 15-20%"
  ]
}
```

---

## 🛡️ **Security Analysis APIs**

### **1. Security Posture Analysis**

#### **Get Security Posture**
```bash
GET /api/security/posture/{cluster_name}
```

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "overall_score": 78,
  "grade": "B+",
  "last_scan": "2025-09-30T10:30:00Z",
  "categories": {
    "network_security": {
      "score": 85,
      "issues": 2,
      "critical": 0,
      "high": 1,
      "medium": 1,
      "findings": [
        {
          "severity": "high",
          "title": "Default network policies not enforced",
          "description": "Cluster allows unrestricted pod-to-pod communication",
          "remediation": "Implement network policies for namespace isolation"
        }
      ]
    },
    "rbac_configuration": {
      "score": 72,
      "issues": 3,
      "findings": [
        {
          "severity": "medium",
          "title": "Overly permissive service account",
          "description": "Default service account has cluster-admin privileges",
          "remediation": "Apply principle of least privilege"
        }
      ]
    },
    "pod_security": {
      "score": 80,
      "issues": 2
    },
    "secrets_management": {
      "score": 65,
      "issues": 4
    }
  }
}
```

### **2. Compliance Checking**

#### **Check Compliance Status**
```bash
GET /api/security/compliance/{cluster_name}
```

**Query Parameters:**
- `framework` (optional): cis, nist, pci, hipaa (default: cis)

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "compliance_framework": "cis",
  "overall_compliance": 82.5,
  "total_controls": 40,
  "passed": 33,
  "failed": 7,
  "categories": [
    {
      "category": "API Server",
      "compliance_percentage": 90.0,
      "controls": [
        {
          "control_id": "CIS-1.1.1",
          "title": "Ensure API server is not accessible from the internet",
          "status": "passed",
          "description": "API server is properly configured with private endpoint"
        },
        {
          "control_id": "CIS-1.1.2", 
          "title": "Ensure API server audit logging is enabled",
          "status": "failed",
          "description": "Audit logging is not configured",
          "remediation": "Enable audit logging in cluster configuration"
        }
      ]
    }
  ]
}
```

### **3. Vulnerability Scanning**

#### **Get Vulnerability Report**
```bash
GET /api/security/vulnerabilities/{cluster_name}
```

**Response:**
```json
{
  "cluster_name": "my-aks-cluster",
  "scan_timestamp": "2025-09-30T10:30:00Z",
  "summary": {
    "total_vulnerabilities": 15,
    "critical": 2,
    "high": 5,
    "medium": 6,
    "low": 2
  },
  "vulnerabilities": [
    {
      "id": "CVE-2024-12345",
      "severity": "critical",
      "title": "Container runtime privilege escalation",
      "description": "Vulnerability in container runtime allows privilege escalation",
      "affected_components": ["containerd"],
      "cvss_score": 9.1,
      "remediation": {
        "action": "Update containerd to version 1.7.8 or higher",
        "patch_available": true,
        "estimated_downtime": "15-30 minutes"
      }
    }
  ]
}
```

---

## 🏢 **Enterprise Management APIs**

### **1. Multi-Subscription Management**

#### **Get Available Subscriptions**
```bash
GET /api/subscriptions
```

**Response:**
```json
{
  "subscriptions": [
    {
      "subscription_id": "abc-123-def",
      "subscription_name": "Production",
      "state": "enabled",
      "is_default": true,
      "clusters_count": 12,
      "monthly_cost": 15750.00
    },
    {
      "subscription_id": "ghi-456-jkl",
      "subscription_name": "Development", 
      "state": "enabled",
      "is_default": false,
      "clusters_count": 5,
      "monthly_cost": 3250.00
    }
  ],
  "total_subscriptions": 2,
  "total_clusters": 17,
  "total_monthly_cost": 19000.00
}
```

#### **Analyze All Subscriptions**
```bash
POST /api/analyze/all-subscriptions
Content-Type: application/json

{
  "analysis_type": "cost_optimization",
  "include_recommendations": true,
  "parallel_processing": true
}
```

### **2. License Management**

#### **Get License Status**
```bash
GET /api/license/status
```

**Response:**
```json
{
  "license_tier": "enterprise",
  "features_enabled": [
    "cost_analysis",
    "ml_insights", 
    "security_analysis",
    "multi_subscription",
    "auto_analysis",
    "implementation_plans"
  ],
  "features_disabled": [],
  "license_expiry": "2026-09-30T23:59:59Z",
  "usage_metrics": {
    "clusters_analyzed": 25,
    "recommendations_generated": 150,
    "implementation_plans_created": 12
  }
}
```

### **3. Auto-Analysis Scheduling**

#### **Configure Auto-Analysis**
```bash
POST /api/schedule/auto-analysis
Content-Type: application/json

{
  "enabled": true,
  "frequency": "daily",
  "time_of_day": "02:00",
  "clusters": ["cluster-1", "cluster-2"],
  "analysis_types": ["cost", "performance", "security"],
  "notification_settings": {
    "email": true,
    "slack": false,
    "webhook_url": "https://your-webhook.com/alerts"
  }
}
```

---

## ⚙️ **Configuration APIs**

### **1. Azure Configuration**

#### **Test Azure Connection**
```bash
POST /api/config/azure/test
Content-Type: application/json

{
  "tenant_id": "your-tenant-id",
  "client_id": "your-client-id", 
  "client_secret": "your-client-secret",
  "subscription_id": "your-subscription-id"
}
```

**Response:**
```json
{
  "connection_status": "success",
  "authenticated": true,
  "permissions_verified": true,
  "accessible_subscriptions": 2,
  "test_results": {
    "cost_management_api": "accessible",
    "monitor_api": "accessible",
    "container_service_api": "accessible",
    "resource_management_api": "accessible"
  }
}
```

### **2. Application Settings**

#### **Get Application Settings**
```bash
GET /api/settings
```

#### **Update Application Settings**
```bash
PUT /api/settings
Content-Type: application/json

{
  "auto_refresh_interval": 300,
  "default_analysis_depth": "comprehensive",
  "cache_ttl_hours": 1,
  "parallel_processing_enabled": true,
  "notification_preferences": {
    "email_alerts": true,
    "cost_threshold_alert": 1000.00,
    "anomaly_detection_sensitivity": "medium"
  }
}
```

---

## 🏥 **Health & Monitoring APIs**

### **1. Application Health**

#### **Basic Health Check**
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-30T10:30:00Z",
  "version": "1.0.0",
  "uptime": "2d 14h 23m 45s"
}
```

#### **Detailed Health Check**
```bash
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-30T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "last_backup": "2025-09-30T02:00:00Z"
    },
    "azure_connectivity": {
      "status": "healthy",
      "response_time_ms": 156,
      "last_successful_call": "2025-09-30T10:29:45Z"
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 0.87,
      "memory_usage_mb": 128
    },
    "background_scheduler": {
      "status": "healthy",
      "active_jobs": 3,
      "last_execution": "2025-09-30T10:00:00Z"
    }
  }
}
```

### **2. Performance Metrics**

#### **Get Application Metrics**
```bash
GET /api/metrics/application
```

**Response:**
```json
{
  "timestamp": "2025-09-30T10:30:00Z",
  "performance": {
    "request_count_24h": 1250,
    "average_response_time_ms": 245,
    "error_rate_24h": 0.02,
    "cache_hit_rate": 0.87
  },
  "resource_usage": {
    "cpu_percent": 15.5,
    "memory_percent": 32.1,
    "disk_usage_percent": 45.7
  },
  "analysis_stats": {
    "clusters_analyzed_24h": 45,
    "recommendations_generated_24h": 128,
    "total_potential_savings_identified": 12500.00
  }
}
```

---

## ⚠️ **Error Handling**

### **Standard Error Response Format**
```json
{
  "error": true,
  "error_code": "CLUSTER_NOT_FOUND",
  "message": "The specified cluster 'my-cluster' was not found",
  "details": {
    "cluster_name": "my-cluster",
    "subscription_id": "abc-123-def",
    "suggestions": [
      "Verify the cluster name spelling",
      "Check if the cluster exists in the specified subscription",
      "Ensure you have access permissions to the cluster"
    ]
  },
  "timestamp": "2025-09-30T10:30:00Z",
  "request_id": "req-abc123def"
}
```

### **Common Error Codes**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CLUSTER_NAME` | 400 | Cluster name contains invalid characters |
| `CLUSTER_NOT_FOUND` | 404 | Specified cluster does not exist |
| `AZURE_AUTH_FAILED` | 401 | Azure authentication failed |
| `INSUFFICIENT_PERMISSIONS` | 403 | Insufficient Azure permissions |
| `ANALYSIS_IN_PROGRESS` | 409 | Analysis already running for this cluster |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `AZURE_API_ERROR` | 502 | Azure API returned an error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### **Error Handling Best Practices**

```bash
# Example with error handling
curl -X GET "http://localhost:5000/api/analyze/cluster/my-cluster" \
  -H "Authorization: Bearer your-token" \
  -w "HTTP Status: %{http_code}\n" \
  -s | jq '.'

# Check for errors in response
if [ $? -ne 0 ]; then
  echo "API request failed"
  exit 1
fi
```

---

## 🚦 **Rate Limiting**

### **Rate Limits**

| Endpoint Category | Requests per Minute | Burst Limit |
|------------------|-------------------|-------------|
| **Analysis APIs** | 10 | 15 |
| **Cost APIs** | 20 | 30 |
| **ML APIs** | 5 | 10 |
| **Configuration APIs** | 30 | 50 |
| **Health APIs** | 60 | 100 |

### **Rate Limit Headers**
```bash
# Response headers
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1698765432
X-RateLimit-Category: analysis
```

### **Rate Limit Exceeded Response**
```json
{
  "error": true,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for analysis APIs",
  "details": {
    "limit": 10,
    "window": "1 minute",
    "reset_time": "2025-09-30T10:31:00Z"
  }
}
```

---

## 📝 **API Usage Examples**

### **Complete Workflow Example**

```bash
#!/bin/bash

# 1. Login and get session
response=$(curl -s -X POST "http://localhost:5000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  -c cookies.txt)

echo "Login response: $response"

# 2. Get all clusters
clusters=$(curl -s -X GET "http://localhost:5000/api/clusters" \
  -b cookies.txt)

echo "Available clusters: $clusters"

# 3. Analyze specific cluster
cluster_name="my-aks-cluster"
analysis=$(curl -s -X GET "http://localhost:5000/api/analyze/cluster/$cluster_name" \
  -b cookies.txt)

echo "Cluster analysis: $analysis"

# 4. Get optimization recommendations
recommendations=$(curl -s -X GET "http://localhost:5000/api/optimize/recommendations/$cluster_name" \
  -b cookies.txt)

echo "Recommendations: $recommendations"

# 5. Generate implementation plan
plan=$(curl -s -X POST "http://localhost:5000/api/generate/implementation-plan" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "cluster_name": "'$cluster_name'",
    "optimization_level": "moderate",
    "timeline_preference": "gradual"
  }')

echo "Implementation plan: $plan"
```

### **Python SDK Example**

```python
import requests
from typing import Dict, List, Optional

class AKSOptimizerClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.session = requests.Session()
        self._login(username, password)
    
    def _login(self, username: str, password: str):
        """Authenticate and establish session"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
    
    def analyze_cluster(self, cluster_name: str, subscription_id: Optional[str] = None) -> Dict:
        """Analyze specific cluster"""
        params = {}
        if subscription_id:
            params['subscription_id'] = subscription_id
            
        response = self.session.get(
            f"{self.base_url}/api/analyze/cluster/{cluster_name}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_recommendations(self, cluster_name: str, category: Optional[str] = None) -> Dict:
        """Get optimization recommendations"""
        params = {}
        if category:
            params['category'] = category
            
        response = self.session.get(
            f"{self.base_url}/api/optimize/recommendations/{cluster_name}",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = AKSOptimizerClient("http://localhost:5000", "admin", "password")

# Analyze cluster
analysis = client.analyze_cluster("my-aks-cluster")
print(f"Monthly cost: ${analysis['cost_analysis']['monthly_cost']}")

# Get recommendations
recommendations = client.get_recommendations("my-aks-cluster", category="cost")
total_savings = recommendations['potential_total_savings']
print(f"Potential savings: ${total_savings}")
```

---

## 🔮 **Future API Enhancements**

### **Planned Features**
- **GraphQL API** - More flexible querying capabilities
- **WebSocket API** - Real-time updates and streaming data
- **Bulk Operations** - Batch analysis and optimization
- **API Versioning** - v2 API with enhanced features
- **OpenAPI/Swagger** - Interactive API documentation

### **Integration Capabilities**
- **Webhook Support** - Event-driven notifications
- **External Tool Integration** - Terraform, Helm, GitOps
- **Custom Metrics** - User-defined optimization metrics
- **Third-party Connectors** - Prometheus, Grafana, Datadog

---

**📚 For more detailed examples and integration guides, see the [README.md](../README.md) and [Development Guide](../DEVELOPMENT-GUIDE.md).**