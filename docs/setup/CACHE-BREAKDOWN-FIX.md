# Cache System Breakdown Data Fix

## 🔍 Problem Summary
AKS Excellence breakdown data (build_quality_breakdown, cost_excellence_breakdown) was disappearing on page refresh, even though it was present on app restart.

## 🎯 Root Cause
The enterprise cache system was **selectively filtering fields** during the cache preparation process, excluding breakdown data from being cached.

### Data Flow Analysis:
1. **Database** → ✅ Had complete breakdown data
2. **Cache Save Input** → ✅ Received complete breakdown data  
3. **Cache Preparation** → ❌ **Filtered out breakdown fields**
4. **Cache Save Output** → ❌ Missing breakdown data
5. **Cache Load** → ❌ Missing breakdown data
6. **Template** → ❌ Missing breakdown data
7. **UI** → ❌ Shows "--" instead of values

## 🔧 Solution Applied

### File: `infrastructure/services/cache_manager.py`
**Function:** `_prepare_cache_data()` (line ~485)

**Added the missing fields:**
```python
# AKS Excellence scores and breakdowns
'build_quality_score': complete_analysis_data.get('build_quality_score'),
'cost_excellence_score': complete_analysis_data.get('cost_excellence_score'),
'build_quality_breakdown': complete_analysis_data.get('build_quality_breakdown'),        # ← ADDED
'cost_excellence_breakdown': complete_analysis_data.get('cost_excellence_breakdown'),    # ← ADDED
'build_quality_details': complete_analysis_data.get('build_quality_details'),          # ← ADDED
'cost_excellence_details': complete_analysis_data.get('cost_excellence_details'),      # ← ADDED
'build_quality_recommendations': complete_analysis_data.get('build_quality_recommendations'), # ← ADDED
'cost_excellence_recommendations': complete_analysis_data.get('cost_excellence_recommendations'), # ← ADDED
```

## 🏗️ How the Cache System Works

### Cache Hierarchy (Priority Order):
1. **Fresh Session Data** - Active analysis sessions
2. **Enterprise Cache** - Fast in-memory cache
3. **Database** - Persistent storage

### Cache Flow:
```
Database Load → Cache Preparation → Cache Save → Cache Load → Template → UI
     ✅              ❌ (WAS)         ❌         ❌        ❌      ❌
     ✅              ✅ (NOW)         ✅         ✅        ✅      ✅
```

### Key Functions:
- **`_get_analysis_data()`** - Loads data from cache hierarchy
- **`save_to_cache_with_validation()`** - Saves data to cache
- **`_prepare_cache_data()`** - **Critical:** Filters which fields get cached
- **`load_from_cache_with_validation()`** - Loads data from cache

## 📋 For Future Implementation

### When Adding New Analysis Fields:

1. **Ensure Database Storage** - Check that new fields are saved in:
   - `infrastructure/persistence/cluster_database.py`
   - `serialize_implementation_plan()` function

2. **Add to Cache Preparation** - **CRITICAL STEP:**
   - Edit `infrastructure/services/cache_manager.py`
   - Function: `_prepare_cache_data()`
   - Add your new fields to the `cache_data` dictionary

3. **Verify Data Flow** - Test that fields persist through:
   - App restart → Page refresh cycle
   - Cache expiration → Database reload cycle

### Example for New Field `my_new_analysis_field`:

```python
# In _prepare_cache_data() function:
cache_data = {
    # ... existing fields ...
    
    # My new analysis fields
    'my_new_analysis_field': complete_analysis_data.get('my_new_analysis_field'),  # ← ADD THIS
    
    # ... rest of fields ...
}
```

## 🔍 Debugging Cache Issues

### Add Debug Logging:
```python
# In _prepare_cache_data():
logger.info(f"🔍 CACHE SAVE: my_field = {complete_analysis_data.get('my_field', 'MISSING')}")

# After cache preparation:
logger.info(f"🔍 CACHE SAVED: my_field = {cache_data.get('my_field', 'MISSING')}")
```

### Check Data Sources:
```python
# In routes.py:
logger.info(f"🔍 ROUTE: Data source = {data_source}")
logger.info(f"🔍 ROUTE: my_field = {cached_analysis.get('my_field', 'MISSING')}")
```

## ⚠️ Common Pitfalls

1. **Forgetting Cache Preparation** - Most common issue
   - New fields get saved to database ✅
   - New fields get loaded from database ✅  
   - New fields get filtered out during cache preparation ❌

2. **Data Type Issues** - Cache preparation expects specific types
   - Use `.get()` with defaults
   - Handle None values appropriately

3. **Template Data Sync** - Ensure template gets complete data
   - Check `analysis=cached_analysis` in route
   - Verify `window.analysisData` in JavaScript

## 🎯 Key Takeaway

**Always check the cache preparation function when adding new analysis fields!**

The cache system is designed for performance and only saves essential fields. Any new analysis data must be explicitly added to the cache preparation whitelist or it will be lost during cache save/load cycles.

---
**Fixed by:** Adding breakdown fields to `_prepare_cache_data()` function  
**Date:** 2025-10-15  
**Impact:** AKS Excellence breakdown details now persist through page refresh