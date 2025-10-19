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
    
    # Base database directory
    BASE_DIR = Path("infrastructure/persistence/database")
    
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