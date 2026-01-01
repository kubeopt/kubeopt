# Smart Caching Implementation

## Overview
Implemented intelligent tiered caching to reduce execution time from 8 minutes while preventing stale data issues.

## Key Features

### 1. Tiered Cache TTLs
Conservative TTLs to ensure data freshness:
- **Real-time metrics (2 min)**: Node/pod CPU and memory usage
- **Dynamic data (5 min)**: Pods, events
- **Semi-dynamic (10 min)**: Deployments, HPA, workloads
- **Semi-static (15 min)**: Nodes, services
- **Static (30 min)**: PVCs, storage, namespaces
- **Mostly static (1 hour)**: ConfigMaps, secrets, RBAC
- **Rarely changes (2 hours)**: Cluster version info

### 2. Selective Refresh
- Only fetches expired batches, not all 14 every time
- Tracks cache timestamps per batch
- Merges cached and fresh data seamlessly

### 3. Cache Efficiency Metrics
- Logs cache hit rate
- Estimates time saved
- Shows which batches are cached vs fetched

### 4. Force Refresh Option
```python
# Normal operation - uses cache
cache.fetch_all_data()

# Force refresh for critical operations
cache.fetch_all_data(force_refresh=True)
```

## Expected Performance Impact

**First run** (all batches expired):
- Fetches all 14 batches: ~8 minutes

**After 2 minutes** (metrics expired):
- Fetches 2 batches (metrics): ~1 minute
- Uses 12 cached batches
- **88% reduction in execution time**

**After 5 minutes** (dynamic data expired):
- Fetches 4 batches (metrics + pods/events): ~2 minutes
- Uses 10 cached batches
- **75% reduction in execution time**

**After 15 minutes** (infrastructure expired):
- Fetches 8 batches: ~4 minutes
- Uses 6 cached batches
- **50% reduction in execution time**

**After 1 hour** (most data expired):
- Fetches 12 batches: ~6 minutes
- Uses 2 cached batches
- **25% reduction in execution time**

## Data Freshness Guarantees

- **Cost-critical data** (metrics, pods): Never older than 5 minutes
- **Infrastructure data** (nodes, services): Never older than 15 minutes
- **Configuration data** (RBAC, config): Never older than 1 hour

## Implementation Details

### Cache Storage
- Raw batch results stored in `self.data[batch_name]`
- Timestamps tracked in `self.cache_timestamps[batch_name]`
- TTLs defined in `self.batch_ttls` dictionary

### Cache Validation
```python
for batch_name, batch_cmd in all_batched_commands.items():
    ttl = self.batch_ttls.get(batch_name, 300)
    age = time.time() - self.cache_timestamps[batch_name]
    if age < ttl:
        # Use cached data
    else:
        # Fetch fresh data
```

## Safety Features

1. **No infinite caching**: All data has maximum TTL of 2 hours
2. **Conservative TTLs**: Shorter than ideal to prevent staleness
3. **Explicit logging**: Shows what's cached vs fetched
4. **Force refresh**: Available for critical operations
5. **Fail on error**: No silent failures per .clauderc

## Usage

The caching is automatic and transparent:
```python
# Creates cache, auto-fetches if configured
cache = KubernetesDataCache(...)

# Subsequent calls use intelligent caching
data = cache.fetch_all_data()  # Only fetches expired batches

# Force refresh when needed
data = cache.fetch_all_data(force_refresh=True)
```

## Monitoring

Look for these log messages:
```
📊 Cache efficiency - 10/14 cached (71% hit rate)
🚀 Fetching 4 expired batches, using 10 cached batches
💰 Saved ~350s by using 10 cached batches
```