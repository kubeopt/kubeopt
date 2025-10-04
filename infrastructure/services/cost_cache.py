#!/usr/bin/env python3
"""
Simple Cost Cache - Just cache Azure API calls for 12 hours to avoid 429 errors
"""

import json
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import pandas as pd

class CostCache:
    def __init__(self, cache_file: str = "infrastructure/persistence/cache/costs.db"):
        self.cache_file = cache_file
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Create simple cache table
        conn = sqlite3.connect(cache_file)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cost_cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                expires TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def _make_key(self, cluster_id: str, subscription_id: str, date_range: str = None) -> str:
        """Make cache key from cluster info"""
        key_data = f"{cluster_id}|{subscription_id}|{date_range or 'current'}"
        return hashlib.md5(key_data.encode()).hexdigest()[:12]
    
    def get(self, cluster_id: str, subscription_id: str, date_range: str = None) -> Optional[Dict[str, Any]]:
        """Get from cache if not expired"""
        key = self._make_key(cluster_id, subscription_id, date_range)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.execute('SELECT data FROM cost_cache WHERE key = ? AND expires > ?', 
                            (key, datetime.now()))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def set(self, cluster_id: str, subscription_id: str, data: Dict[str, Any], 
            date_range: str = None, hours: int = 12):
        """Cache data for specified hours"""
        key = self._make_key(cluster_id, subscription_id, date_range)
        expires = datetime.now() + timedelta(hours=hours)
        
        conn = sqlite3.connect(self.cache_file)
        conn.execute('INSERT OR REPLACE INTO cost_cache (key, data, expires) VALUES (?, ?, ?)',
                    (key, json.dumps(data), expires))
        conn.commit()
        conn.close()
    
    def clear_expired(self):
        """Remove expired entries"""
        conn = sqlite3.connect(self.cache_file)
        conn.execute('DELETE FROM cost_cache WHERE expires < ?', (datetime.now(),))
        conn.commit()
        conn.close()

def _prepare_data_for_cache(data: Any) -> Dict[str, Any]:
    """Convert DataFrame to cacheable format"""
    if isinstance(data, pd.DataFrame):
        # Convert DataFrame to dict format for JSON serialization
        return {
            '_type': 'dataframe',
            '_data': data.to_dict('records'),
            '_columns': list(data.columns),
            '_index': list(data.index) if not data.index.equals(pd.RangeIndex(len(data))) else None
        }
    elif isinstance(data, dict):
        # Already serializable
        return data
    else:
        # Try to convert to dict, fallback to string representation
        try:
            return {'_type': 'other', '_data': str(data)}
        except:
            return {'_type': 'error', '_data': 'Could not serialize data'}

def _restore_data_from_cache(cached_data: Dict[str, Any]) -> Any:
    """Restore DataFrame from cached format"""
    if isinstance(cached_data, dict) and cached_data.get('_type') == 'dataframe':
        # Restore DataFrame from cached format
        df = pd.DataFrame(cached_data['_data'])
        if cached_data.get('_index') is not None:
            df.index = cached_data['_index']
        return df
    elif isinstance(cached_data, dict) and cached_data.get('_type') == 'other':
        # Return string representation
        return cached_data['_data']
    else:
        # Return as-is (regular dict)
        return cached_data

# Global cache instance
cache = CostCache()

def check_database_cost_freshness(cluster_name: str, max_age_hours: int = 12) -> Optional[pd.DataFrame]:
    """
    Check if we have fresh cost data in the database to avoid unnecessary Azure API calls
    
    Args:
        cluster_name: Name of the cluster to check
        max_age_hours: Maximum age in hours to consider data fresh (default 12)
    
    Returns:
        DataFrame with cost data if fresh, None if stale or missing
    """
    try:
        # Connect to cluster database
        cluster_db = 'infrastructure/persistence/database/clusters.db'
        if not os.path.exists(cluster_db):
            return None
            
        conn = sqlite3.connect(cluster_db)
        cursor = conn.execute('''
            SELECT last_cost, last_savings, last_analyzed, analysis_data 
            FROM clusters 
            WHERE name = ? AND last_analyzed IS NOT NULL AND last_cost > 0
        ''', (cluster_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        last_cost, last_savings, last_analyzed, analysis_data = row
        
        # Check if data is fresh enough
        analyzed_time = datetime.fromisoformat(last_analyzed)
        age_hours = (datetime.now() - analyzed_time).total_seconds() / 3600
        
        if age_hours <= max_age_hours:
            # Data is fresh, create a DataFrame in the expected format
            
            # Try to get full analysis data first - use stored cost DataFrame if available
            cost_df_data = []
            if analysis_data:
                try:
                    full_analysis = json.loads(analysis_data.decode('utf-8'))
                    # If we have stored cost DataFrame data, use it directly
                    if isinstance(full_analysis, dict) and 'cost_data' in full_analysis:
                        cost_df_data = full_analysis.get('cost_data', [])
                        print(f"🎯 Found stored cost DataFrame: {len(cost_df_data)} entries")
                except:
                    pass  # If analysis data can't be decoded, continue with basic data
            
            # If no detailed cost data stored, return None to force fresh Azure API call
            if not cost_df_data:
                print(f"❌ No stored cost DataFrame found, forcing fresh Azure API call")
                return None
            
            # Create DataFrame from stored Azure cost data
            cost_df = pd.DataFrame(cost_df_data)
            print(f"✅ Restored original Azure cost DataFrame: {cost_df.shape[0]} rows, {cost_df.shape[1]} columns")
            
            # Add cache metadata attributes to DataFrame
            cost_df._from_cache = True
            cost_df._from_database = True  
            cost_df._database_cache_hit = True
            cost_df._age_hours = age_hours
            cost_df._last_analyzed = last_analyzed
            
            # Add comprehensive metadata
            cost_df.attrs.update({
                'total_cost': last_cost,
                'total_savings': last_savings,
                'last_analyzed': last_analyzed,
                'age_hours': age_hours,
                'data_source': 'Database Cache',
                'from_database': True,
                'cache_hit': True
            })
            
            return cost_df
        else:
            # Data is stale
            return None
            
    except Exception as e:
        # If there's any error checking the database, return None to fall back to API
        return None

def cached_cost_fetch(cluster_id: str, subscription_id: str, fetch_func: Callable, 
                     date_range: str = None, max_age_hours: int = 12, **kwargs) -> Dict[str, Any]:
    """
    Smart cached wrapper with database-first validation to avoid unnecessary Azure API calls
    
    Strategy:
    1. Check database for fresh cost data (< max_age_hours old)
    2. Check file cache for recent API responses  
    3. Make fresh Azure API call only if needed
    
    Args:
        cluster_id: Cluster identifier
        subscription_id: Azure subscription ID
        fetch_func: Function to call if cache miss
        date_range: Date range for caching key
        max_age_hours: Maximum age to consider database data fresh (default 12)
    """
    
    # STEP 1: Check database first for fresh cost data
    db_data = check_database_cost_freshness(cluster_id, max_age_hours)
    if db_data is not None:
        age_hours = getattr(db_data, '_age_hours', 'unknown')
        print(f"🎯 DATABASE HIT: Using {age_hours:.1f}h old cost data for {cluster_id}")
        return db_data
    
    # STEP 2: Try file cache for recent API responses
    cached = cache.get(cluster_id, subscription_id, date_range)
    if cached:
        # Restore DataFrame from cache if needed
        restored_data = _restore_data_from_cache(cached)
        
        # Add cache metadata (only if data is not None)
        if restored_data is not None:
            if hasattr(restored_data, '__dict__'):  # DataFrame
                restored_data._from_cache = True
            elif isinstance(restored_data, dict):  # Dict
                restored_data['_from_cache'] = True
            
        return restored_data
    
    # STEP 3: Both database and file cache miss - fetch from Azure API (last resort)
    print(f"❌ CACHE MISS: Database and file cache both stale/empty for {cluster_id}, calling Azure API")
    # Cache miss - fetch from API
    try:
        data = fetch_func(cluster_id, subscription_id, date_range, **kwargs)
        
        # Only cache if data is not None
        if data is not None:
            # Handle DataFrame serialization for caching
            cacheable_data = _prepare_data_for_cache(data)
            
            # Cache the result
            cache.set(cluster_id, subscription_id, cacheable_data, date_range)
        
        # Add cache metadata to original data (only if data is not None)
        if data is not None:
            if hasattr(data, '__dict__'):  # DataFrame
                data._from_cache = False
            elif isinstance(data, dict):  # Dict
                data['_from_cache'] = False
        
        return data
        
    except Exception as e:
        # If API fails, try to use expired cache
        if '429' in str(e):
            # Get any cached data, even if expired
            key = cache._make_key(cluster_id, subscription_id, date_range)
            conn = sqlite3.connect(cache.cache_file)
            cursor = conn.execute('SELECT data FROM cost_cache WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                stale_data = json.loads(row[0])
                
                # Restore DataFrame from cache if needed
                restored_stale_data = _restore_data_from_cache(stale_data)
                
                # Add cache metadata (only if data is not None)
                if restored_stale_data is not None:
                    if hasattr(restored_stale_data, '__dict__'):  # DataFrame
                        restored_stale_data._from_cache = True
                        restored_stale_data._stale = True
                    elif isinstance(restored_stale_data, dict):  # Dict
                        restored_stale_data['_from_cache'] = True
                        restored_stale_data['_stale'] = True
                    
                return restored_stale_data
        
        raise