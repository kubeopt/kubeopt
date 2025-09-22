# 🔄 Clean Architecture Migration Examples

## After Testing Current Hybrid - Use These Examples to Clean Up

---

## 📝 **Example 1: enterprise_metrics.py**

### **Before (Current Hybrid):**
```python
from app.shared.kubernetes_data_cache import fetch_cluster_data

class MLFrameworkGenerator:
    def __init__(self, cluster_name, resource_group, subscription_id):
        self.cluster_name = cluster_name
        # ... other init
        self.kubectl_executor = SubscriptionAwareKubectlExecutor(...)  # REMOVE
    
    async def _gather_cluster_data(self) -> Dict[str, Any]:
        cache = fetch_cluster_data(self.cluster_name, self.resource_group, self.subscription_id)
        results = cache.get_workload_data()
        resource_data = cache.get_resource_usage_data()
        # ... complex cache queries
        return results
```

### **After (Clean):**
```python
from app.shared.kubernetes_data_service import get_kubernetes_data_service

class MLFrameworkGenerator:
    def __init__(self, cluster_name, resource_group, subscription_id):
        self.cluster_name = cluster_name
        # ... other init  
        # NO kubectl_executor!
    
    async def _gather_cluster_data(self) -> Dict[str, Any]:
        data_service = get_kubernetes_data_service(
            self.cluster_name, self.resource_group, self.subscription_id
        )
        return data_service.get_enterprise_metrics_data()  # Clean, simple!
```

---

## 📝 **Example 2: aks_realtime_metrics.py**

### **Before (Current Hybrid):**
```python
class AKSRealTimeMetricsFetcher:
    def execute_kubectl_command(self, kubectl_cmd: str, timeout: int = 60):
        # Try cache first, fallback to direct kubectl
        if hasattr(self, 'cache'):
            cache_result = self._try_get_from_cache(kubectl_cmd)
            if cache_result is not None:
                return cache_result
        return self._execute_kubectl_direct(kubectl_cmd, timeout)
    
    def _try_get_from_cache(self, kubectl_cmd: str):
        # Complex mapping logic...
        if "kubectl top nodes" in kubectl_cmd:
            return cache_data.get('node_usage', '')
        # ... many more mappings
    
    def get_node_metrics(self):
        self.cache.fetch_all_data()
        cache_data = self.cache.get_resource_usage_data()
        top_nodes = cache_data.get('node_usage', '')
        node_info = cache_data.get('nodes', {})
        # ... processing logic
```

### **After (Clean):**
```python
from app.shared.kubernetes_data_service import get_kubernetes_data_service

class AKSRealTimeMetricsFetcher:
    # NO execute_kubectl_command method!
    # NO _try_get_from_cache method!
    # NO cache logic!
    
    def get_node_metrics(self):
        data_service = get_kubernetes_data_service(
            self.cluster_name, self.resource_group, self.subscription_id
        )
        
        # Clean, direct data access
        top_nodes = data_service.get_node_usage()
        node_info = data_service.get_nodes()
        # ... same processing logic
```

---

## 📝 **Example 3: pod_cost_analyzer.py**

### **Before (Current Hybrid):**
```python
class EnhancedDynamicCostDistributionEngine:
    def __init__(self, resource_group, cluster_name, subscription_id):
        self.kubectl_executor = SubscriptionAwareKubectlExecutor(...)  # REMOVE
        self.cache = get_or_create_cache(...)  # REMOVE
    
    def _safe_kubectl_command(self, kubectl_cmd: str, timeout: int = None):
        # Try cache first for common commands
        if hasattr(self, 'cache'):
            cache_result = self._try_get_from_cache(kubectl_cmd)
            if cache_result is not None:
                return cache_result
        return self.kubectl_executor.execute_command(kubectl_cmd, timeout)
    
    def _collect_enhanced_resource_data(self):
        self.cache.fetch_all_data()
        cache_data = self.cache.get_cost_analysis_data()
        # ... complex cache manipulation
```

### **After (Clean):**
```python
from app.shared.kubernetes_data_service import get_kubernetes_data_service

class EnhancedDynamicCostDistributionEngine:
    def __init__(self, resource_group, cluster_name, subscription_id):
        # NO kubectl_executor!
        # NO cache!
        self.data_service = get_kubernetes_data_service(cluster_name, resource_group, subscription_id)
    
    # NO _safe_kubectl_command method!
    # NO _try_get_from_cache method!
    
    def _collect_enhanced_resource_data(self):
        # Clean, direct access
        return self.data_service.get_cost_analysis_data()
```

---

## 🔧 **Migration Steps**

### **Step 1: Update Imports**
```python
# REMOVE these imports:
from app.shared.kubernetes_data_cache import fetch_cluster_data, get_or_create_cache
from app.analytics.pod_cost_analyzer import SubscriptionAwareKubectlExecutor

# ADD this import:
from app.shared.kubernetes_data_service import get_kubernetes_data_service
```

### **Step 2: Remove kubectl Methods**
Delete these methods completely:
- `execute_kubectl_command()`
- `_safe_kubectl_command()`
- `_try_get_from_cache()`
- `_execute_kubectl_direct()`

### **Step 3: Remove kubectl Dependencies**
```python
# REMOVE from __init__:
self.kubectl_executor = SubscriptionAwareKubectlExecutor(...)
self.cache = get_or_create_cache(...)

# NO REPLACEMENTS NEEDED - just delete them!
```

### **Step 4: Replace Data Access**
```python
# BEFORE:
cache = fetch_cluster_data(...)
data = cache.get_workload_data()

# AFTER:
data_service = get_kubernetes_data_service(cluster, rg, sub)
data = data_service.get_enterprise_metrics_data()
```

---

## ✅ **Verification Checklist**

After migration, verify:

### **1. No kubectl Commands Outside Data Service**
```bash
grep -r "kubectl" --include="*.py" . | grep -v "kubernetes_data_service.py" | grep -v "kubernetes_data_cache.py"
# Should return NO results from your main components
```

### **2. No Direct kubectl Execution**
```bash
grep -r "execute_kubectl" --include="*.py" .
# Should return NO results except in old backup files
```

### **3. Clean Import Structure**
All components should only import:
```python
from app.shared.kubernetes_data_service import get_kubernetes_data_service
```

### **4. Performance Same or Better**
Run performance test - should be identical or faster than hybrid approach.

---

## 🎯 **Final Clean Architecture**

```
app/
├── shared/
│   ├── kubernetes_data_service.py       ← ONLY file with kubectl
│   └── kubernetes_data_cache.py         ← Cache implementation (internal)
├── ml/
│   └── enterprise_metrics.py        ← NO kubectl, clean queries
├── analytics/
│   ├── aks_realtime_metrics.py          ← NO kubectl, clean queries
│   └── pod_cost_analyzer.py             ← NO kubectl, clean queries
└── ...
```

**Result**: Single source of truth + same performance + much cleaner code! 🚀