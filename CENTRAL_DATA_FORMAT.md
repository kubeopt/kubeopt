# AKS Cost Optimizer - Central Data Format Specification

## Overview
This document defines the single, unified data format for the entire AKS Cost Optimizer system. All components must use this format for consistency, data integrity, and system-wide compatibility.

## Core Principles
1. **Single Source of Truth**: One format for each data type across all components
2. **Consistent Identifiers**: Standard naming conventions for all fields
3. **Forward Compatibility**: Extensible structure for future enhancements
4. **Type Safety**: Clear data types and validation rules
5. **Standard Attributes**: Common fields across all entities

## 1. Global Identifiers & Metadata

### Standard Cluster Identity
```python
{
    "cluster_identity": {
        "cluster_id": str,           # Primary key: unique identifier
        "cluster_name": str,         # Azure AKS cluster name
        "resource_group": str,       # Azure resource group
        "subscription_id": str,      # Azure subscription ID
        "region": str,              # Azure region (e.g., "eastus2")
        "environment": str          # "dev", "staging", "prod"
    }
}
```

### Standard Timestamps
```python
{
    "timestamps": {
        "analysis_timestamp": str,   # ISO format: "2025-09-15T10:30:00Z"
        "data_collection_timestamp": str,
        "last_updated": str,
        "cache_expires_at": str
    }
}
```

### Standard Metadata
```python
{
    "metadata": {
        "data_version": str,         # Format version: "v2.0"
        "source_system": str,        # "realtime_metrics", "cost_analyzer", etc.
        "confidence_score": float,   # 0.0 to 1.0
        "data_completeness": float,  # 0.0 to 1.0
        "validation_status": str     # "valid", "warning", "invalid"
    }
}
```

## 2. Workload Data Format

### Standard Workload Entity
```python
{
    "workload_id": str,             # Unique: "{namespace}/{name}/{type}"
    "name": str,                    # Workload name
    "namespace": str,               # Kubernetes namespace
    "workload_type": str,           # "deployment", "statefulset", "daemonset"
    "labels": dict,                 # Kubernetes labels
    "resource_requirements": {
        "cpu_request": float,       # CPU cores requested
        "memory_request": int,      # Memory bytes requested
        "cpu_limit": float,         # CPU cores limit
        "memory_limit": int         # Memory bytes limit
    },
    "current_utilization": {
        "cpu_percentage": float,    # Current CPU utilization %
        "memory_percentage": float, # Current memory utilization %
        "cpu_cores_used": float,    # Actual CPU cores used
        "memory_bytes_used": int    # Actual memory bytes used
    },
    "scaling_config": {
        "has_hpa": bool,
        "current_replicas": int,
        "min_replicas": int,
        "max_replicas": int,
        "target_cpu_percentage": float
    }
}
```

## 3. Cost Data Format

### Standard Cost Analysis
```python
{
    "cost_analysis": {
        "cluster_identity": {}, # Standard cluster identity
        "timestamps": {},       # Standard timestamps
        "metadata": {},         # Standard metadata
        
        "total_cost": {
            "monthly_total": float,      # Total monthly cost in USD
            "daily_average": float,      # Average daily cost
            "cost_trend": str           # "increasing", "stable", "decreasing"
        },
        
        "cost_breakdown": {
            "compute": {
                "node_cost": float,
                "node_count": int,
                "node_types": list
            },
            "storage": {
                "storage_cost": float,
                "storage_gb": float,
                "storage_types": dict
            },
            "networking": {
                "networking_cost": float,
                "egress_gb": float
            },
            "control_plane": {
                "control_plane_cost": float
            },
            "additional_services": {
                "registry_cost": float,
                "monitoring_cost": float,
                "other_cost": float
            }
        },
        
        "optimization_opportunities": {
            "total_potential_savings": float,
            "savings_breakdown": {
                "hpa_optimization": {
                    "monthly_savings": float,
                    "confidence": float,
                    "implementation_effort": str # "low", "medium", "high"
                },
                "rightsizing": {
                    "monthly_savings": float,
                    "confidence": float,
                    "implementation_effort": str
                },
                "storage_optimization": {
                    "monthly_savings": float,
                    "confidence": float,
                    "implementation_effort": str
                },
                "infrastructure": {
                    "monthly_savings": float,
                    "confidence": float,
                    "implementation_effort": str
                },
                "container_data": {
                    "monthly_savings": float,
                    "confidence": float,
                    "implementation_effort": str
                },
                "security_monitoring": {
                    "monthly_savings": float,
                    "confidence": float,
                    "implementation_effort": str
                }
            }
        }
    }
}
```

## 4. Performance & Resource Data Format

### High CPU Workloads (Standardized)
```python
{
    "high_cpu_workloads": [
        {
            "workload_id": str,         # Standard workload ID
            "name": str,
            "namespace": str,
            "workload_type": str,       # "hpa", "deployment", "pod"
            "cpu_utilization": float,   # Current CPU percentage
            "target_cpu": float,        # Target CPU percentage
            "severity": str,            # "low", "moderate", "high", "critical"
            "replicas": {
                "current": int,
                "min": int,
                "max": int
            },
            "recommendations": {
                "action": str,          # "scale_up", "optimize_app", "investigate"
                "priority": str,        # "low", "medium", "high", "critical"
                "estimated_savings": float
            }
        }
    ]
}
```

### Resource Utilization Summary
```python
{
    "resource_utilization": {
        "cluster_identity": {},     # Standard cluster identity
        "timestamps": {},           # Standard timestamps
        "metadata": {},             # Standard metadata
        
        "overall_metrics": {
            "total_workloads": int,
            "total_nodes": int,
            "total_pods": int,
            "cluster_cpu_utilization": float,
            "cluster_memory_utilization": float
        },
        
        "utilization_gaps": {
            "cpu_gap_percentage": float,    # Over/under-provisioning gap
            "memory_gap_percentage": float,
            "waste_cost_monthly": float
        },
        
        "efficiency_scores": {
            "current_health_score": float,  # 0-100 based on CNCF standards
            "target_health_score": float,
            "optimization_potential": float
        },
        
        "standards_compliance": {
            "cncf_compliance": bool,
            "finops_compliance": bool,
            "optimization_opportunities_percentage": float
        }
    }
}
```

## 5. HPA & Scaling Data Format

### Standard HPA Analysis
```python
{
    "hpa_analysis": {
        "cluster_identity": {},     # Standard cluster identity
        "timestamps": {},           # Standard timestamps
        "metadata": {},             # Standard metadata
        
        "hpa_summary": {
            "total_hpas": int,
            "hpa_coverage_percentage": float,   # % of workloads with HPA
            "target_coverage": float,           # CNCF standard: 80%
            "optimization_score": float
        },
        
        "hpa_workloads": [
            {
                "workload_id": str,     # Standard workload ID
                "hpa_name": str,
                "namespace": str,
                "target_resource": str,  # deployment/statefulset name
                "metrics": [
                    {
                        "type": str,    # "Resource", "Pods", "Object"
                        "resource": str, # "cpu", "memory"
                        "target_type": str, # "Utilization", "AverageValue"
                        "target_value": float
                    }
                ],
                "current_status": {
                    "current_replicas": int,
                    "desired_replicas": int,
                    "min_replicas": int,
                    "max_replicas": int,
                    "current_cpu_utilization": float,
                    "target_cpu_utilization": float
                },
                "performance_category": str, # "optimal", "underutilized", "overutilized", "critical"
                "optimization_potential": {
                    "monthly_savings": float,
                    "recommended_action": str
                }
            }
        ],
        
        "high_cpu_workloads": [], # Uses standard high CPU format above
        
        "recommendations": {
            "create_hpa": [],       # Workloads that need HPA
            "optimize_hpa": [],     # HPAs that need tuning
            "investigate": []       # HPAs with issues
        }
    }
}
```

## 6. Analysis Results Format

### Complete Analysis Result
```python
{
    "aks_analysis_result": {
        "cluster_identity": {},     # Standard cluster identity
        "timestamps": {},           # Standard timestamps
        "metadata": {},             # Standard metadata
        
        "analysis_status": {
            "status": str,          # "completed", "partial", "failed"
            "completion_percentage": float,
            "errors": [],
            "warnings": []
        },
        
        "cost_analysis": {},        # Uses standard cost format
        "resource_utilization": {}, # Uses standard resource format
        "hpa_analysis": {},         # Uses standard HPA format
        
        "workloads": [             # All workloads using standard format
            {} # Standard workload entity
        ],
        
        "optimization_summary": {
            "total_monthly_savings": float,
            "optimization_percentage": float,
            "payback_period_months": float,
            "implementation_timeline": str,
            "risk_assessment": str     # "low", "medium", "high"
        },
        
        "recommendations": {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": []
        }
    }
}
```

## 7. Implementation Guidelines

### Data Validation Rules
1. All monetary values in USD
2. All percentages as floats (0-100 scale)
3. All timestamps in ISO 8601 format
4. All IDs must be unique and consistent
5. Required fields must never be null
6. Confidence scores: 0.0 to 1.0

### Component Integration
1. **Data Producers**: Must output in central format
2. **Data Consumers**: Must accept central format only
3. **Data Storage**: Store in central format
4. **API Endpoints**: Return central format
5. **UI Components**: Consume central format

### Migration Strategy
1. Create format conversion utilities
2. Update one component at a time
3. Maintain backward compatibility temporarily
4. Remove legacy formats after migration
5. Add validation at all data boundaries

This central format ensures consistency, reduces data transformation overhead, and provides a single source of truth for the entire system.