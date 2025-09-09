# CPU Optimization Plan Generator - Organization-Agnostic Solution

## 🎯 Overview

The CPU Optimization Plan Generator creates customized, executable optimization plans for Kubernetes clusters based on configurable organization-specific thresholds. It supports any organization, cloud provider, and operational methodology.

## 🔧 Key Features

### ✅ **Organization-Agnostic Design**
- **Configurable Thresholds**: Customize CPU utilization triggers per organization
- **Multi-Cloud Support**: Generic templates for Azure, AWS, GCP, and on-premises
- **Risk-Based Commands**: Categorized by risk level with safety controls
- **Flexible Severity Levels**: Adaptable based on organization tolerance

### ✅ **Scenario Detection**
- **Critical Overutilization**: Emergency response for extreme CPU usage
- **High Usage**: Optimization for elevated CPU consumption
- **Inefficient Allocation**: Right-sizing and efficiency improvements
- **Workload Imbalance**: Load distribution optimization
- **Resource Contention**: Multi-pod competition resolution
- **Scaling Issues**: Auto-scaling configuration and tuning

### ✅ **Generic Command Templates**
- **Template-Based**: Placeholder commands for easy customization
- **Multi-Cloud Compatible**: Provider-agnostic Kubernetes commands
- **Safety Controls**: Risk assessment and validation steps
- **Rollback Capabilities**: Rollback commands for high-risk actions

## 📋 Organization Profiles

### 1. **Conservative Enterprise**
```python
config = {
    'critical_cpu_threshold': 150,      # Lower threshold - more conservative
    'target_cpu_utilization': 60,       # Lower target utilization
    'enable_emergency_actions': False,  # Disable high-risk actions
    'max_replica_scale': 10            # Conservative scaling
}
```

### 2. **Aggressive Startup**
```python
config = {
    'critical_cpu_threshold': 300,      # Higher threshold - more aggressive
    'target_cpu_utilization': 80,       # Higher target utilization
    'enable_emergency_actions': True,   # Enable all optimizations
    'max_replica_scale': 50            # Aggressive scaling
}
```

### 3. **Cost-Optimized**
```python
config = {
    'critical_cpu_threshold': 180,      # Balanced for cost efficiency
    'target_cpu_utilization': 70,       # Cost-performance balance
    'cost_efficiency_factor': 0.6,      # Higher cost savings focus
    'max_replica_scale': 20            # Reasonable scaling
}
```

## 🚀 Usage Examples

### Basic Usage
```python
from ml.cpu_optimization_planner import create_cpu_optimization_planner

# Use default configuration
planner = create_cpu_optimization_planner()

# CPU metrics from your monitoring system
cpu_metrics = {
    'average_cpu_usage': 85.0,
    'peak_cpu_usage': 150.0,
    'cpu_efficiency': 60.0,
    'high_cpu_workloads': 5,
    'total_pods': 20,
    'monthly_cost': 1200.0,
    'optimization_potential_pct': 30.0,
    'critical_alerts': 2,
    'nodes_count': 4
}

# Generate optimization plan
plan = planner.generate_optimization_plan('my-cluster-id', cpu_metrics)

print(f"Scenario: {plan.scenario.value}")
print(f"Commands: {len(plan.optimization_commands)}")
print(f"Estimated Savings: ${plan.estimated_savings['estimated_monthly_savings_usd']}/month")
```

### Organization-Specific Configuration
```python
# Custom configuration for your organization
org_config = {
    'critical_cpu_threshold': 120,          # Trigger optimization at 120% CPU
    'high_cpu_threshold': 75,               # High usage at 75% CPU
    'target_cpu_utilization': 65,           # Target 65% utilization
    'organization_name': 'Acme Corporation',
    'cloud_provider': 'azure',              # Azure-specific optimizations
    'enable_emergency_actions': False,      # Conservative approach
    'max_replica_scale': 15,                # Limit scaling to 15 replicas
    'default_cpu_limit': '800m',            # 800 millicores default limit
    'cost_efficiency_factor': 0.35         # Conservative cost estimates
}

planner = create_cpu_optimization_planner(org_config)
```

### Pre-built Profiles
```python
from config.cpu_optimization_config import get_config_by_profile

# Use pre-built organization profiles
conservative_config = get_config_by_profile('conservative')
aggressive_config = get_config_by_profile('aggressive')
cost_config = get_config_by_profile('cost-optimized')
devops_config = get_config_by_profile('devops')

# Create planner with chosen profile
planner = create_cpu_optimization_planner(conservative_config)
```

## 📊 Export Options

### Executable Script
```python
# Export as executable bash script
script_path = planner.export_plan_to_script(optimization_plan)
# Creates: /tmp/cpu_optimization_cluster-name_20240907_120000.sh
```

### JSON Configuration
```python
# Export as JSON for automation
json_path = planner.export_plan_to_json(optimization_plan)
# Creates: /tmp/cpu_optimization_plan_cluster-name_20240907_120000.json
```

### Comprehensive Reports
```python
from reporting.cpu_report_exporter import create_cpu_report_exporter

exporter = create_cpu_report_exporter()
report_path = exporter.export_comprehensive_report(report_data, 'pdf')
# Available formats: 'pdf', 'excel', 'json', 'csv'
```

## 🔗 API Integration

### Generate Optimization Plan
```bash
GET /api/clusters/{cluster_id}/cpu-optimization-plan
```

### Download Executable Script
```bash
GET /api/clusters/{cluster_id}/cpu-optimization-script
```

### Export Reports
```bash
GET /api/clusters/{cluster_id}/cpu-report?format=pdf
GET /api/clusters/{cluster_id}/cpu-report?format=excel
GET /api/clusters/{cluster_id}/cpu-report?format=json
GET /api/clusters/{cluster_id}/cpu-report?format=csv
```

## 📋 Sample Generated Commands

### Assessment Commands (All Organizations)
```bash
# Check current node resource utilization
kubectl top nodes --context your-cluster

# Identify top CPU consuming pods
kubectl top pods --all-namespaces --sort-by=cpu --context your-cluster

# Review existing resource limits
kubectl get limitrange --all-namespaces --context your-cluster
```

### Emergency Actions (High CPU Scenarios)
```bash
# TEMPLATE: Apply emergency CPU limits
kubectl patch deployment <DEPLOYMENT_NAME> -n <NAMESPACE> -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "<CONTAINER_NAME>",
          "resources": {
            "limits": {"cpu": "1000m"},
            "requests": {"cpu": "500m"}
          }
        }]
      }
    }
  }
}'

# TEMPLATE: Create HPA for auto-scaling
kubectl autoscale deployment <DEPLOYMENT_NAME> --cpu-percent=70 --min=2 --max=20 -n <NAMESPACE>
```

### Multi-Cloud Node Scaling Templates
```bash
# Azure AKS
az aks nodepool scale --cluster-name <CLUSTER_NAME> --name <NODEPOOL_NAME> --resource-group <RESOURCE_GROUP> --node-count <NEW_COUNT>

# AWS EKS  
aws eks update-nodegroup-config --cluster-name <CLUSTER_NAME> --nodegroup-name <NODEGROUP_NAME> --scaling-config minSize=<MIN>,maxSize=<MAX>,desiredSize=<DESIRED>

# GCP GKE
gcloud container clusters resize <CLUSTER_NAME> --num-nodes=<NEW_COUNT> --zone=<ZONE>
```

## 🎛️ Configuration Options

### CPU Thresholds
- `critical_cpu_threshold`: CPU % that triggers emergency response (default: 200%)
- `high_cpu_threshold`: CPU % that triggers high usage optimization (default: 80%)
- `target_cpu_utilization`: Target CPU utilization after optimization (default: 70%)
- `peak_critical_threshold`: Peak CPU % for critical scenarios (default: 400%)
- `peak_high_threshold`: Peak CPU % for high usage scenarios (default: 150%)

### Organization Settings
- `organization_name`: Name for customized reporting
- `cloud_provider`: 'azure', 'aws', 'gcp', or 'multi' for generic templates
- `cluster_naming_pattern`: 'auto' to detect from cluster ID

### Safety Settings
- `enable_emergency_actions`: Allow high-risk emergency commands (default: true)
- `require_manual_confirmation`: Add confirmation prompts (default: true)
- `max_replica_scale`: Maximum replicas for autoscaling (default: 20)

### Resource Limits
- `default_cpu_request`: Default CPU request for templates (default: '100m')
- `default_cpu_limit`: Default CPU limit for templates (default: '1000m')
- `default_memory_request`: Default memory request (default: '128Mi')
- `default_memory_limit`: Default memory limit (default: '2Gi')

## 🔍 Testing

Run the test suite to see different scenarios:

```bash
# Test generic scenarios
python3 test_generic_cpu_optimization.py

# Test with different organization profiles
python3 -c "
from ml.cpu_optimization_planner import create_cpu_optimization_planner
from config.cpu_optimization_config import get_config_by_profile

config = get_config_by_profile('conservative')
planner = create_cpu_optimization_planner(config)
# ... test with your metrics
"
```

## 💡 Best Practices

### 1. **Start Conservative**
Begin with lower thresholds and gradually increase based on comfort level

### 2. **Test in Development**
Always test optimization plans in development environments first

### 3. **Monitor Impact**
Use the provided monitoring commands to track optimization effectiveness

### 4. **Customize for Your Organization**
Adjust thresholds based on your organization's risk tolerance and operational needs

### 5. **Review High-Risk Commands**
Always review high-risk commands before execution, especially in production

## 🆘 Emergency Response

For critical CPU scenarios, the system generates immediate response plans:

1. **Assessment**: Rapid cluster analysis
2. **Emergency Limits**: Immediate CPU constraints for runaway workloads
3. **Scale Up**: Node pool scaling to handle load
4. **Load Balancing**: Pod distribution optimization
5. **Monitoring**: Continuous observation setup

## 📈 Expected Results

Based on organization profile and current CPU usage:

- **Conservative**: 15-30% CPU reduction, moderate cost savings
- **Aggressive**: 30-60% CPU reduction, maximum cost savings
- **Cost-Optimized**: 20-40% CPU reduction, focused cost efficiency
- **DevOps**: 25-45% CPU reduction, automation-friendly approach

The solution adapts to any organization's needs while providing actionable, executable optimization plans.