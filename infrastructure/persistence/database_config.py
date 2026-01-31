#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Database Configuration for Unified Architecture
"""

import os
from pathlib import Path
from typing import Dict

class DatabaseConfig:
    """Configuration for the unified database architecture"""
    
    # REQUIRE persistent volume - no fallbacks
    volume_mount = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
    if volume_mount:
        BASE_DIR = Path(volume_mount)
    elif Path('/data').exists():
        # Standard volume mount location
        BASE_DIR = Path('/data')
    else:
        # NO FALLBACK - volume is required
        raise ValueError(
            "CRITICAL: No persistent volume detected! "
            "Please attach a volume to this service at /data mount path. "
            "Without a volume, all data will be lost on restart."
        )
    
    # Ensure directory exists
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Unified database paths
    DATABASES = {
        # Core databases
        'alerts': BASE_DIR / 'alerts.db',
        'clusters': BASE_DIR / 'clusters.db', 
        'costs': BASE_DIR / 'costs.db',
        'learning_data': BASE_DIR / 'learning_data.db'
    }
    
    # Machine learning database paths (clean architecture)
    ML_DATABASES = {
        'enhanced_learning': 'machine_learning/data/enhanced_learning.db',
        'learning_data': 'machine_learning/data/learning_data.db',
        'optimization_learning': 'machine_learning/data/optimization_learning.db'
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