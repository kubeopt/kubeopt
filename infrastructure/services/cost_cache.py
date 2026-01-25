#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
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
        
        if row is not None and row:
            return json.loads(row[0])
        return None
    
    def set(self, cluster_id: str, subscription_id: str, data: Dict[str, Any], 
            date_range: str = None, hours: int = None):
        """Cache data for specified hours"""
        if hours is None:
            # Get cache duration from settings
            try:
                from infrastructure.services.settings_manager import settings_manager
                hours = int(settings_manager.get_setting('COST_CACHE_HOURS', '6'))
            except:
                hours = 6  # Default fallback
        
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
        try:
            return {'_type': 'other', '_data': str(data)}
        except Exception as e:
            raise RuntimeError(f"Operation failed: {e}") from e
            # {'_type': 'error', '_data': 'Could not serialize data'}

def _restore_data_from_cache(cached_data: Dict[str, Any]) -> Any:
    """Restore DataFrame from cached format"""
    if isinstance(cached_data, dict) and cached_data.get('_type') == 'dataframe':
        # Restore DataFrame from cached format
        df = pd.DataFrame(cached_data['_data'])
        if cached_data.get('_index') is not None:
            df.index = cached_data['_index']
        return df
    elif isinstance(cached_data, dict) and cached_data.get('_type') == 'other':
        return cached_data['_data']
    else:
        return cached_data

# Global cache instance
cache = CostCache()

def check_database_cost_freshness(cluster_name: str, max_age_hours: int = None) -> Optional[pd.DataFrame]:
    """
    Check if we have fresh cost data in the database to avoid unnecessary Azure API calls
    
    Args:
        cluster_name: Name of the cluster to check (can be full cluster ID or just cluster name)
        max_age_hours: Maximum age in hours to consider data fresh (from settings)
    
    Returns:
        DataFrame with cost data if fresh, None if stale or missing
    """
    if max_age_hours is None:
        # Get cache duration from settings
        try:
            from infrastructure.services.settings_manager import settings_manager
            max_age_hours = int(settings_manager.get_setting('COST_CACHE_HOURS', '6'))
        except:
            max_age_hours = 6  # Default fallback
            
    try:
        # Connect to cluster database using environment variable
        cluster_db = os.getenv('DATABASE_PATH', 'infrastructure/persistence/database/clusters.db')
        if not os.path.exists(cluster_db):
            return None
            
        conn = sqlite3.connect(cluster_db)
        
        # Try exact match first - use cost_fetched_at for cost cache validation
        cursor = conn.execute('''
            SELECT last_cost, last_savings, cost_fetched_at, analysis_data 
            FROM clusters 
            WHERE name = ? AND cost_fetched_at IS NOT NULL AND last_cost > 0
        ''', (cluster_name,))
        
        row = cursor.fetchone()
        
        # If no exact match and cluster_name contains underscore (looks like full cluster ID),
        # try extracting just the cluster name part
        if not row and '_' in cluster_name:
            # Extract cluster name from formats like "rg-xxx_cluster-name" 
            cluster_name_only = cluster_name.split('_')[-1]  # Get last part after underscore
            print(f"🔍 Cache lookup: No exact match for '{cluster_name}', trying cluster name only: '{cluster_name_only}'")
            
            cursor = conn.execute('''
                SELECT last_cost, last_savings, cost_fetched_at, analysis_data 
                FROM clusters 
                WHERE name = ? AND cost_fetched_at IS NOT NULL AND last_cost > 0
            ''', (cluster_name_only,))
            
            row = cursor.fetchone()
            
        # If still no match, try pattern matching for cluster names contained in the cluster_name
        if not row:
            cursor = conn.execute('''
                SELECT last_cost, last_savings, cost_fetched_at, analysis_data 
                FROM clusters 
                WHERE ? LIKE '%' || name || '%' AND cost_fetched_at IS NOT NULL AND last_cost > 0
                ORDER BY cost_fetched_at DESC
                LIMIT 1
            ''', (cluster_name,))
            
            row = cursor.fetchone()
            if row is not None and row:
                print(f"🔍 Cache lookup: Found match using pattern matching for '{cluster_name}'")
        
        conn.close()
        
        if not row:
            return None
            
        last_cost, last_savings, cost_fetched_at, analysis_data = row
        
        # Check if COST data is fresh enough based on cost_fetched_at timestamp
        if not cost_fetched_at:
            print(f"❌ No cost_fetched_at timestamp for '{cluster_name}' - treating as cache miss")
            return None
            
        cost_fetch_time = datetime.fromisoformat(cost_fetched_at)
        age_hours = (datetime.now() - cost_fetch_time).total_seconds() / 3600
        
        if age_hours <= max_age_hours:
            # Data is fresh, create a DataFrame in the expected format
            
            # Try to get full analysis data first - use stored cost DataFrame if available
            cost_df_data = []
            if analysis_data is not None and analysis_data:
                try:
                    full_analysis = json.loads(analysis_data.decode('utf-8'))
                    # If we have stored cost DataFrame data, use it directly
                    if isinstance(full_analysis, dict) and 'cost_data' in full_analysis:
                        cost_df_data = full_analysis.get('cost_data', [])
                        print(f"🎯 Found stored cost DataFrame: {len(cost_df_data)} entries")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    raise  # If analysis data can't be decoded, continue with basic data
            
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
            cost_df._cost_fetched_at = cost_fetched_at
            
            # Add comprehensive metadata
            cost_df.attrs.update({
                'total_cost': last_cost,
                'total_savings': last_savings,
                'cost_fetched_at': cost_fetched_at,
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
                     date_range: str = None, max_age_hours: int = None, **kwargs) -> Dict[str, Any]:
    """
    Direct Azure API wrapper - database cache disabled to ensure fresh data
    
    Strategy:
    1. Always make fresh Azure API call
    2. Database cache disabled due to stale data issues
    
    Args:
        cluster_id: Cluster identifier
        subscription_id: Azure subscription ID
        fetch_func: Function to call if cache miss
        date_range: Date range for caching key
        max_age_hours: Maximum age to consider database data fresh (from settings)
    """
    # DISABLED: Database cache check - always fetch fresh data
    # The database was returning stale $27.22 data instead of correct $15 data
    
    # Always fetch fresh from Azure API
    print(f"🔄 Fetching fresh cost data from Azure API for {cluster_id}")
    try:
        data = fetch_func(cluster_id, subscription_id, date_range, **kwargs)
        
        # Add cache metadata to indicate fresh fetch
        if data is not None:
            if hasattr(data, '__dict__'):  # DataFrame
                data._from_cache = False
            elif isinstance(data, dict):  # Dict
                data['_from_cache'] = False
        
        return data
        
    except Exception as e:
        print(f"❌ Azure API call failed for {cluster_id}: {e}")
        raise