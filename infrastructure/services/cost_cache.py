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

def cached_cost_fetch(cluster_id: str, subscription_id: str, fetch_func: Callable, 
                     date_range: str = None, **kwargs) -> Dict[str, Any]:
    """
    Simple cached wrapper for your existing cost fetch functions
    
    Usage:
        # Instead of:
        # cost_data = your_cost_function(cluster_id, subscription_id)
        
        # Use:
        cost_data = cached_cost_fetch(cluster_id, subscription_id, your_cost_function)
    """
    
    # Try cache first
    cached = cache.get(cluster_id, subscription_id, date_range)
    if cached:
        # Restore DataFrame from cache if needed
        restored_data = _restore_data_from_cache(cached)
        
        # Add cache metadata
        if hasattr(restored_data, '__dict__'):  # DataFrame
            restored_data._from_cache = True
        else:  # Dict
            restored_data['_from_cache'] = True
            
        return restored_data
    
    # Cache miss - fetch from API
    try:
        data = fetch_func(cluster_id, subscription_id, date_range, **kwargs)
        
        # Handle DataFrame serialization for caching
        cacheable_data = _prepare_data_for_cache(data)
        
        # Cache the result
        cache.set(cluster_id, subscription_id, cacheable_data, date_range)
        
        # Add cache metadata to original data
        if hasattr(data, '__dict__'):  # DataFrame
            data._from_cache = False
        else:  # Dict
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
                
                # Add cache metadata
                if hasattr(restored_stale_data, '__dict__'):  # DataFrame
                    restored_stale_data._from_cache = True
                    restored_stale_data._stale = True
                else:  # Dict
                    restored_stale_data['_from_cache'] = True
                    restored_stale_data['_stale'] = True
                    
                return restored_stale_data
        
        raise