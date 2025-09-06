# Configurable Environment System

## Overview
The AKS Cost Optimizer now supports **fully configurable environments** allowing customers to customize scoring metrics based on their organizational environment structure and requirements. This eliminates the previous issue of equivalent scores across different environments.

## Problem Solved
**Before**: Dev and UAT clusters showed identical scores because they used static industry benchmarks
**After**: Each environment is scored against appropriate targets based on its purpose (experimentation vs stability)

## Key Features

### 1. Dynamic Environment Detection
- **Smart Alias Mapping**: Automatically detects environments using configurable aliases
- **Database Integration**: Uses cluster database environment settings when available
- **Fallback Logic**: Intelligent name-based detection when database info unavailable

### 2. Customizable Environment Types
Customers can define any environments they need:
```json
"sandbox": ["sbx", "test", "playground"]
"development": ["dev", "develop"] 
"qa": ["qa", "qc", "quality", "testing"]
"staging": ["stg", "uat", "preprod", "pre-prod"]
"production": ["prod", "prd", "live"]
```

### 3. Environment-Specific Scoring Targets

Each environment can have unique configurations:

| Metric | Development | Staging | Production |
|--------|------------|---------|------------|
| **Deployment Frequency** | 0.5/day (innovation) | 0.2/day (validation) | 0.1/day (stability) |
| **Failure Tolerance** | 20% (learning) | 10% (pre-prod) | 2% (reliability) |
| **Capacity Buffer** | 40% (experimentation) | 25% (load testing) | 20% (optimization) |
| **Compliance Minimum** | 60% (basic) | 80% (higher) | 95% (strict) |
| **Utilization Target** | 50% (flexibility) | 70% (efficiency) | 75% (optimized) |

### 4. Configurable Scoring Weights

Different environments prioritize different metrics:
- **Development**: 60% velocity, 20% stability, 20% churn (innovation-focused)
- **Staging**: 40% velocity, 40% stability, 20% churn (balanced)
- **Production**: 20% velocity, 60% stability, 20% churn (reliability-focused)

## Configuration File Structure

Location: `/config/environments.json`

```json
{
  "environments": {
    "environment_name": {
      "aliases": ["alias1", "alias2", "alias3"],
      "deployment_frequency_target": 0.5,
      "change_failure_tolerance": 0.20,
      "capacity_buffer_target": 40.0,
      "compliance_minimum": 60.0,
      "utilization_target": 50.0,
      "velocity_weight": 0.6,
      "stability_weight": 0.2,
      "churn_weight": 0.2,
      "color": "#17a2b8",
      "description": "Environment description"
    }
  },
  "default_environment": "development"
}
```

### Required Fields
- `deployment_frequency_target`: Target deployments per day
- `change_failure_tolerance`: Maximum acceptable failure rate (0.0-1.0)
- `capacity_buffer_target`: Days of capacity runway target
- `compliance_minimum`: Minimum compliance score percentage
- `utilization_target`: Target resource utilization percentage
- `velocity_weight`: Weight for velocity in composite scoring (0.0-1.0)
- `stability_weight`: Weight for stability in composite scoring (0.0-1.0)
- `churn_weight`: Weight for churn in composite scoring (0.0-1.0)

### Optional Fields
- `aliases`: Array of cluster name patterns for detection
- `color`: UI color code for environment badge
- `description`: Human-readable environment description

## API Endpoints

### Get Current Environment Configuration
```bash
GET /api/environments
```

**Response:**
```json
{
  "status": "success",
  "environments": { ... },
  "default_environment": "development",
  "total_environments": 5
}
```

### Update Environment Configuration
```bash
POST /api/environments
Content-Type: application/json

{
  "environments": {
    "sandbox": {
      "aliases": ["sbx", "test"],
      "deployment_frequency_target": 1.0,
      "change_failure_tolerance": 0.30,
      "capacity_buffer_target": 50.0,
      "compliance_minimum": 40.0,
      "utilization_target": 40.0,
      "velocity_weight": 0.8,
      "stability_weight": 0.1,
      "churn_weight": 0.1
    }
  },
  "default_environment": "development"
}
```

## Customer Use Cases

### Scenario 1: Traditional Enterprise
```json
{
  "development": ["dev", "develop"],
  "staging": ["stg", "uat"], 
  "production": ["prod", "live"]
}
```

### Scenario 2: DevOps-Heavy Organization
```json
{
  "sandbox": ["sbx", "playground"],
  "development": ["dev", "feature"],
  "integration": ["int", "ci"],
  "qa": ["qa", "test"],
  "staging": ["stage", "uat"],
  "preprod": ["preprod", "pre"],
  "production": ["prod", "live"]
}
```

### Scenario 3: Agile Teams
```json
{
  "experimental": ["exp", "poc"],
  "development": ["dev", "sprint"],
  "testing": ["test", "qa"],
  "demo": ["demo", "showcase"],
  "production": ["prod", "release"]
}
```

## Implementation Details

### Environment Detection Logic
1. **Database Lookup**: Check `clusters.environment` field first
2. **Alias Matching**: Match cluster name against configured aliases
3. **Default Fallback**: Use configured default environment
4. **Logging**: Track detection decisions for debugging

### Scoring Algorithm Changes
- **Capacity Planning**: Uses environment-specific utilization targets
- **Compliance**: Applies environment-appropriate minimum thresholds  
- **Team Velocity**: Weights velocity vs stability based on environment purpose
- **Operational Maturity**: Evaluates against environment-specific deployment targets

### Real-Time Configuration Updates
- **Hot Reload**: Config changes apply immediately without restart
- **Cache Invalidation**: Automatic config cache refresh on updates
- **Thread Safety**: Concurrent access protection during config updates

## Benefits for SaaS Customers

1. **Accurate Scoring**: Each environment evaluated against appropriate standards
2. **Customizable**: Adapt to any organizational environment structure  
3. **Meaningful Insights**: Development prioritizes innovation, production prioritizes stability
4. **Cost Optimization**: Environment-appropriate recommendations maximize ROI
5. **No Code Changes**: Customers configure via API or config file

## Migration Guide

Existing installations will automatically:
1. Use fallback environment detection based on cluster names
2. Apply reasonable default baselines
3. Maintain backward compatibility with current scoring

To customize environments:
1. Access the `/api/environments` endpoint
2. Define your organization's environment structure
3. Set appropriate scoring targets for each environment
4. Update aliases to match your cluster naming conventions

## Technical Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Cluster Names  │───▶│ Environment      │───▶│ Scoring Engine  │
│  (Detection)    │    │ Configuration    │    │ (Targets)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Customer Config  │
                       │ environments.json│
                       └──────────────────┘
```

This configurable system ensures your SaaS customers get accurate, environment-appropriate cost optimization recommendations that reflect their actual operational priorities and constraints.