"""
Configuration and Global Setup
"""

import sys
import os
from pathlib import Path
import threading
import logging
from datetime import datetime
import sqlite3

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Thread-safe analysis storage
_analysis_sessions = {}
_analysis_lock = threading.Lock()
analysis_status_tracker = {}
analysis_results = {}

# Enhanced global cache with TTL
analysis_cache = {
    'clusters': {},  # {cluster_id: {'data': {}, 'timestamp': str, 'ttl_hours': int}}
    'global_ttl_hours': 1
}

# Initialize database components
from app.data.cluster_database import EnhancedClusterManager, migrate_from_json
from app.ml.implementation_generator import AKSImplementationGenerator

enhanced_cluster_manager = EnhancedClusterManager()
implementation_generator = AKSImplementationGenerator()

def enhance_database_schema():
    """Add analysis status tracking to database"""
    try:
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            # Add analysis status columns if they don't exist
            conn.execute('''
                ALTER TABLE clusters ADD COLUMN analysis_status TEXT DEFAULT 'pending'
            ''')
            conn.execute('''
                ALTER TABLE clusters ADD COLUMN analysis_progress INTEGER DEFAULT 0
            ''')
            conn.execute('''
                ALTER TABLE clusters ADD COLUMN analysis_message TEXT DEFAULT ''
            ''')
            conn.execute('''
                ALTER TABLE clusters ADD COLUMN analysis_started_at TIMESTAMP NULL
            ''')
            conn.commit()
            logger.info("✅ Enhanced database schema for analysis tracking")
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    except Exception as e:
        logger.error(f"❌ Database schema enhancement failed: {e}")

def initialize_database():
    """Initialize database and migrate from JSON if exists"""
    try:
        # Check if old clusters.json exists and migrate
        if os.path.exists('clusters.json'):
            logger.info("🔄 Migrating from JSON to SQLite database")
            migrate_from_json('clusters.json', enhanced_cluster_manager)
        
        logger.info("✅ Database initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

# Initialize database schema
enhance_database_schema()

# Initialize alerts system
try:
    from app.alerts.alerts_manager import (
        EnhancedAlertsManager, 
        init_enhanced_alerts_service, 
        shutdown_enhanced_alerts_service
    )
    ALERTS_AVAILABLE = True
    logger.info("✅ Alerts manager imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Alerts manager not available: {e}")
    ALERTS_AVAILABLE = False

# Global alerts manager (will be initialized later)
alerts_manager = None