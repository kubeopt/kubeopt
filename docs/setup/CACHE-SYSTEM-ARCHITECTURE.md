# AKS Cost Optimizer Cache System Architecture

## 🏗️ Cache System Overview

The cache system has **3 layers** with **priority-based fallback**:

```
Request → Fresh Session → Enterprise Cache → Database → Response
   ↓           ↓              ↓              ↓         ↓
  API      (Memory)      (Memory)       (SQLite)   Template
```

## 📁 Key Files & Their Roles

### 1. **Data Retrieval Layer**
**File:** `shared/utils/shared.py`
- **Function:** `_get_analysis_data(cluster_id)`
- **Purpose:** Main entry point for all data requests
- **Logic:** Checks sources in priority order

```python
def _get_analysis_data(cluster_id) -> Tuple[Optional[Dict], str]:
    # Priority 1: Fresh session data (active analysis)
    # Priority 2: Enterprise cache (fast memory)  
    # Priority 3: Database (persistent storage)
```

### 2. **Cache Management Layer**
**File:** `infrastructure/services/cache_manager.py`

#### Key Functions:
- **`save_to_cache_with_validation()`** - Main cache save entry point
- **`_prepare_cache_data()`** - ⚠️ **CRITICAL:** Field filtering happens here
- **`load_from_cache_with_validation()`** - Main cache load entry point
- **`is_cache_valid()`** - Cache expiration checking

### 3. **Database Layer**
**File:** `infrastructure/persistence/cluster_database.py`
- **Function:** `get_latest_analysis(cluster_id)`
- **Storage:** SQLite with BLOB serialization
- **Serialization:** `serialize_implementation_plan()` / `deserialize_implementation_plan()`

### 4. **API/Route Layer**
**File:** `presentation/api/routes.py`
- **Route:** `/cluster/<cluster_id>` (dashboard)
- **Route:** `/api/cluster/<cluster_id>/aks-excellence` (API)
- **Function:** Calls `_get_analysis_data()` and passes to template

### 5. **Frontend Layer**
**File:** `presentation/web/static/js/aks-excellence.js`
- **Source:** `window.analysisData` (from template)
- **Function:** `loadAKSScores()` - Processes analysis data for UI

## 🔄 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA GENERATION                              │
├─────────────────────────────────────────────────────────────────┤
│ analytics/processors/aks_scorer.py                             │
│ ├─ generate_aks_score()                                         │
│ ├─ Result: { build_quality_breakdown: {...}, ... }             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE STORAGE                              │
├─────────────────────────────────────────────────────────────────┤
│ infrastructure/persistence/cluster_database.py                 │
│ ├─ save_analysis_results()                                      │
│ ├─ serialize_implementation_plan()                              │
│ ├─ Storage: SQLite BLOB (preserves ALL fields)                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA RETRIEVAL                               │
├─────────────────────────────────────────────────────────────────┤
│ shared/utils/shared.py                                          │
│ ├─ _get_analysis_data(cluster_id)                               │
│ ├─ Priority 1: _analysis_sessions (fresh)                      │
│ ├─ Priority 2: enterprise_cache (memory)                       │
│ ├─ Priority 3: cluster_database (persistent)                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE PROCESSING                             │
├─────────────────────────────────────────────────────────────────┤
│ infrastructure/services/cache_manager.py                       │
│ ├─ save_to_cache_with_validation()                              │
│ ├─ _prepare_cache_data() ⚠️ FIELD FILTERING HERE               │
│ ├─ load_from_cache_with_validation()                            │
│ └─ Result: Filtered data (only whitelisted fields)             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTE/API LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│ presentation/api/routes.py                                      │
│ ├─ single_cluster_dashboard()                                   │
│ ├─ get_aks_excellence_data()                                    │
│ └─ Calls: _get_analysis_data(cluster_id)                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPLATE RENDERING                           │
├─────────────────────────────────────────────────────────────────┤
│ presentation/web/templates/unified_dashboard.html               │
│ ├─ window.analysisData = {{ analysis | tojson }}               │
│ └─ Passes data to JavaScript                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND PROCESSING                          │
├─────────────────────────────────────────────────────────────────┤
│ presentation/web/static/js/aks-excellence.js                   │
│ ├─ loadAKSScores()                                              │
│ ├─ formatBreakdownForUI()                                       │
│ └─ updateScoreBreakdown()                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Cache System Configuration

### Global Cache Configuration
**File:** `shared/config/config.py`
```python
analysis_cache = {
    'clusters': {},  # {cluster_id: {'data': {}, 'timestamp': str, 'subscription_id': str}}
    'subscriptions': {},  # {subscription_id: {'clusters': [], 'last_updated': str}}
    'global_ttl_hours': 0.10,  # Cache expiration time
    'subscription_isolation_enabled': True
}
```

### Cache Key Strategy
**File:** `infrastructure/services/cache_manager.py`
**Class:** `CacheKeyStrategy`
- **Function:** `generate_cache_key(cluster_id, subscription_id)`
- **Format:** `{subscription_id}_{cluster_id}`

## 🚨 Troubleshooting Guide

### Problem: "Data disappears on page refresh"

#### Step 1: Check Data Source
**File:** `presentation/api/routes.py`
**Add Debug:**
```python
logger.info(f"🔍 ROUTE: Data source = {data_source}")
logger.info(f"🔍 ROUTE: my_field = {cached_analysis.get('my_field', 'MISSING')}")
```

**Expected Sources:**
- **App Restart:** `cluster_database` (complete data)
- **Page Refresh:** `enterprise_cache` (filtered data)

#### Step 2: Check Cache Preparation
**File:** `infrastructure/services/cache_manager.py`
**Function:** `_prepare_cache_data()`
**Add Debug:**
```python
# Before cache preparation
logger.info(f"🔍 CACHE SAVE: my_field = {complete_analysis_data.get('my_field', 'MISSING')}")

# After cache preparation  
logger.info(f"🔍 CACHE SAVED: my_field = {cache_data.get('my_field', 'MISSING')}")
```

#### Step 3: Check Database Storage
**File:** `infrastructure/persistence/cluster_database.py`
**Function:** `get_latest_analysis()`
**Add Debug:**
```python
logger.info(f"🔍 DATABASE LOAD: my_field = {analysis_data.get('my_field', 'MISSING')}")
```

#### Step 4: Check Frontend Data
**File:** `presentation/web/static/js/aks-excellence.js`
**Add Debug:**
```javascript
console.log('🔍 Frontend my_field:', analysisData.my_field);
```

### Problem: "Cache not expiring properly"

#### Check Cache Validity
**File:** `infrastructure/services/cache_manager.py`
**Function:** `is_cache_valid(cluster_id)`
**Debug:**
```python
logger.info(f"🔍 CACHE CHECK: TTL = {analysis_cache['global_ttl_hours']} hours")
```

### Problem: "Data not persisting to database"

#### Check Serialization
**File:** `infrastructure/persistence/cluster_database.py`
**Function:** `serialize_implementation_plan()`
**Verify:** All fields are JSON serializable

## 🔧 How to Add New Cached Fields

### 1. Ensure Database Storage
**File:** `infrastructure/persistence/cluster_database.py`
- Verify field is included in `serialize_implementation_plan()`
- Check field is preserved in `deserialize_implementation_plan()`

### 2. Add to Cache Preparation ⚠️ CRITICAL
**File:** `infrastructure/services/cache_manager.py`
**Function:** `_prepare_cache_data()`
```python
cache_data = {
    # ... existing fields ...
    'my_new_field': complete_analysis_data.get('my_new_field'),  # ← ADD HERE
    # ... rest of fields ...
}
```

### 3. Add Cache Validation (if needed)
**File:** `infrastructure/services/cache_manager.py`
**Function:** `_validate_cache_data_structure()`
```python
if not data.get('my_new_field'):
    errors.append("Missing my_new_field")
```

### 4. Test Data Flow
1. **Generate** new field in analysis
2. **Save** to database
3. **Cache** the data
4. **Restart** app → **Refresh** page
5. **Verify** field persists

## 📊 Cache Performance Monitoring

### Cache Hit/Miss Tracking
**File:** `shared/utils/shared.py`
**Function:** `_get_analysis_data()`
- Returns `data_source` indicating where data came from
- `fresh_session` = Best performance
- `enterprise_cache` = Good performance  
- `cluster_database` = Slower, triggers cache save

### Cache Statistics
**File:** `infrastructure/services/cache_manager.py`
**Global Variable:** `analysis_cache['clusters']`
- Check cache size: `len(analysis_cache['clusters'])`
- Check cache keys: `analysis_cache['clusters'].keys()`

## 🔒 Cache Security & Isolation

### Subscription Isolation
**File:** `infrastructure/services/cache_manager.py`
**Feature:** Each subscription gets isolated cache namespace
**Key Format:** `{subscription_id}_{cluster_id}`

### Cache Cleanup
**File:** `infrastructure/services/cache_manager.py`
**Function:** `_cache_key_lookup` cleanup (keeps last 100 entries)

---

## 🎯 Quick Reference

| **Issue** | **Check File** | **Look For** |
|-----------|----------------|--------------|
| Data missing on refresh | `cache_manager.py` | `_prepare_cache_data()` |
| Wrong data source | `shared.py` | `_get_analysis_data()` priority order |
| Database issues | `cluster_database.py` | `serialize_implementation_plan()` |
| Frontend missing data | `aks-excellence.js` | `window.analysisData` |
| Cache not expiring | `cache_manager.py` | `is_cache_valid()` + `global_ttl_hours` |

**Remember:** The cache system is **performance-optimized** and **field-selective**. Always check the cache preparation whitelist when adding new analysis data!