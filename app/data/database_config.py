#!/usr/bin/env python3
"""
Database Configuration for Unified Architecture
"""

import os
from pathlib import Path
from typing import Dict

class DatabaseConfig:
    """Configuration for the unified database architecture"""
    
    # Base database directory
    BASE_DIR = Path("app/data/database")
    
    # Unified database paths
    DATABASES = {
        # Core databases (keep existing)
        'alerts': BASE_DIR / 'alerts.db',
        'clusters': BASE_DIR / 'clusters.db',
        
        # New unified databases
        'ml_analytics': BASE_DIR / 'ml_analytics.db',
        'security_analytics': BASE_DIR / 'security_analytics.db', 
        'operational_data': BASE_DIR / 'operational_data.db'
    }
    
    # Legacy database paths (for migration reference)
    LEGACY_DATABASES = {
        'enhanced_learning': 'app/ml/data_feed/enhanced_learning.db',
        'learning_data': 'app/ml/data_feed/learning_data.db',
        'optimization_learning': 'app/ml/data_feed/optimization_learning.db',
        'compliance': 'app/security/data/compliance.db',
        'offline_security': 'app/security/data/offline_security.db',
        'security_posture': 'app/security/data/security_posture.db'
    }
    
    @classmethod
    def get_database_path(cls, db_name: str) -> str:
        """Get the path for a specific database"""
        if db_name in cls.DATABASES:
            return str(cls.DATABASES[db_name])
        raise ValueError(f"Unknown database: {db_name}")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all database directories exist"""
        cls.BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_connection_string(cls, db_name: str) -> str:
        """Get SQLite connection string for a database"""
        return f"sqlite:///{cls.get_database_path(db_name)}"