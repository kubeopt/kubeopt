#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Updated Configuration and Global Setup for Multi-Subscription AKS Cost Optimization
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

# Configure enhanced logging for multi-subscription
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
        #logging.FileHandler('multi_subscription_analysis.log')  # Separate log for subscription analysis
    ]
)

# Suppress verbose Azure SDK HTTP logging
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.core.pipeline').setLevel(logging.WARNING)
logging.getLogger('azure.mgmt').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ALERTS_AVAILABLE = True
# Thread-safe analysis storage with subscription awareness
_analysis_sessions = {}
_analysis_lock = threading.Lock()
analysis_status_tracker = {}
analysis_results = {}

try:
    from analytics.collectors.aks_config_fetcher import create_cluster_config_fetcher
    CLUSTER_CONFIG_AVAILABLE = True
    logger.info("✅ Cluster configuration fetcher available")
except ImportError as e:
    CLUSTER_CONFIG_AVAILABLE = False
    logger.warning(f"⚠️ Cluster configuration fetcher not available: {e}")


# Enhanced global cache with multi-subscription support
analysis_cache = {
    'clusters': {},  # {cluster_id: {'data': {}, 'timestamp': str, 'ttl_hours': int, 'subscription_id': str}}
    'subscriptions': {},  # {subscription_id: {'clusters': [], 'last_updated': str}}
    'global_ttl_hours': 0.10,
    'subscription_isolation_enabled': True
}

# Initialize enhanced database components with multi-subscription support
from infrastructure.persistence.cluster_database import EnhancedMultiSubscriptionClusterManager, migrate_database_for_multi_subscription
from infrastructure.plan_generation.claude_plan_generator import AIImplementationPlanGenerator

# Use the enhanced multi-subscription cluster manager
enhanced_cluster_manager = EnhancedMultiSubscriptionClusterManager()

# Initialize implementation generator conditionally
implementation_generator = None
try:
    implementation_generator = AIImplementationPlanGenerator()
    logger.info("✅ AI plan generator initialized")
except ValueError as e:
    if "ANTHROPIC_API_KEY" in str(e):
        logger.warning("⚠️ Claude API plan generator not available - API key required")
        implementation_generator = None
    else:
        raise

def initialize_multi_subscription_environment():
    """Initialize the multi-subscription environment"""
    try:
        logger.info("🌐 Initializing multi-subscription AKS Cost Optimization environment...")
        
        # Initialize subscription manager
        from infrastructure.services.subscription_manager import azure_subscription_manager
        
        # Get available subscriptions and initialize tracking
        subscriptions = azure_subscription_manager.get_available_subscriptions(force_refresh=True)
        logger.info(f"🌐 Discovered {len(subscriptions)} Azure subscriptions")
        
        # Initialize subscription tracking in cache
        for sub in subscriptions:
            analysis_cache['subscriptions'][sub.subscription_id] = {
                'subscription_name': sub.subscription_name,
                'clusters': [],
                'last_updated': datetime.now().isoformat(),
                'is_default': sub.is_default,
                'state': sub.state
            }
        
        # Initialize background maintenance
        from infrastructure.services.background_processor import schedule_subscription_analysis_maintenance
        schedule_subscription_analysis_maintenance()
        
        logger.info("✅ Multi-subscription environment initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize multi-subscription environment: {e}")
        return False

def enhance_database_schema_for_multi_subscription():
    """Enhanced database schema setup for multi-subscription support"""
    try:
        # Run the comprehensive migration
        migration_success = migrate_database_for_multi_subscription(enhanced_cluster_manager.db_path)
        
        if migration_success:
            logger.info("✅ Multi-subscription database schema enhanced successfully")
            
            # Validate schema
            with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['clusters', 'analysis_results', 'subscriptions', 
                                 'subscription_analysis_sessions', 'subscription_performance']
                
                missing_tables = [t for t in expected_tables if t not in tables]
                if missing_tables:
                    logger.warning(f"⚠️ Missing tables after migration: {missing_tables}")
                else:
                    logger.info("✅ All required tables present after migration")
            
            return True
        else:
            logger.error("❌ Multi-subscription database schema enhancement failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database schema enhancement failed: {e}")
        return False

def initialize_database():
    """Initialize database with multi-subscription support"""
    try:
        # Check if old clusters.json exists and migrate
        if os.path.exists('clusters.json'):
            logger.info("🔄 Migrating from JSON to multi-subscription SQLite database")
            from infrastructure.persistence.cluster_database import migrate_from_json
            migrate_from_json('clusters.json', enhanced_cluster_manager)
        
        # Run multi-subscription schema enhancement
        enhance_database_schema_for_multi_subscription()
        
        # Initialize security database tables
        try:
            from infrastructure.security.database_schema import initialize_security_database
            logger.debug("🔒 Initializing security database schema...")
            security_init_success = initialize_security_database()
            if security_init_success:
                logger.debug("✅ Security database initialization completed")
            else:
                logger.warning("⚠️ Security database initialization failed - using existing tables")
        except Exception as security_e:
            logger.warning(f"⚠️ Security database initialization error: {security_e}")
        
        # Initialize operational database tables
        try:
            logger.debug("📊 Initializing operational database schema...")
            from infrastructure.persistence.database_config import DatabaseConfig
            import sqlite3
            
            operational_db_path = DatabaseConfig.get_database_path('operational_data')
            with sqlite3.connect(operational_db_path) as conn:
                cursor = conn.cursor()
                
                # Create security_scan_results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_scan_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        result_id TEXT UNIQUE NOT NULL,
                        cluster_id TEXT NOT NULL,
                        resource_group TEXT,
                        cluster_name TEXT NOT NULL,
                        scan_timestamp TEXT NOT NULL,
                        analysis_data TEXT,
                        confidence REAL DEFAULT 0.0,
                        frameworks_analyzed TEXT,
                        based_on_real_data BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create cost_analysis_history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cost_analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cluster_id TEXT NOT NULL,
                        analysis_date TEXT NOT NULL,
                        total_cost REAL NOT NULL,
                        compute_cost REAL DEFAULT 0.0,
                        storage_cost REAL DEFAULT 0.0,
                        network_cost REAL DEFAULT 0.0,
                        potential_savings REAL DEFAULT 0.0,
                        optimization_opportunities TEXT,
                        cost_breakdown TEXT,
                        currency TEXT DEFAULT 'USD',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create performance_metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cluster_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_unit TEXT,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_scan_results_cluster ON security_scan_results(cluster_name, scan_timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_analysis_cluster ON cost_analysis_history(cluster_id, analysis_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_metrics_cluster ON performance_metrics(cluster_id, timestamp)')
                
                conn.commit()
                
            logger.info("✅ Operational database initialization completed")
        except Exception as operational_e:
            logger.warning(f"⚠️ Operational database initialization error: {operational_e}")
        
        # Initialize subscription tracking
        enhanced_cluster_manager.initialize_subscription_tracking()
        
        logger.info("✅ Multi-subscription database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-subscription database initialization failed: {e}")
        return False

def setup_subscription_aware_analysis_engine():
    """Setup the multi-subscription analysis engine"""
    try:
        from infrastructure.persistence.processing.analysis_engine import multi_subscription_analysis_engine
        
        # Validate analysis engine is ready
        if hasattr(multi_subscription_analysis_engine, 'run_subscription_aware_analysis'):
            logger.info("✅ Multi-subscription analysis engine ready")
            return True
        else:
            logger.error("❌ Multi-subscription analysis engine not properly configured")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Failed to import multi-subscription analysis engine: {e}")
        return False

def initialize_subscription_aware_alerts():
    """Initialize alerts system with subscription awareness"""
    global alerts_manager
    
    try:
        from infrastructure.services.enhanced_alerts_manager import initialize_alerts_system
        
        # Initialize with subscription support
        alerts_manager = initialize_alerts_system()
        
        if alerts_manager:
            logger.info("✅ Subscription-aware alerts manager initialized successfully")
            return True
        else:
            logger.warning("⚠️ Alerts manager not available - subscription-aware alerts disabled")
            return False
            
    except ImportError as e:
        logger.warning(f"⚠️ Subscription-aware alerts manager not available: {e}")
        alerts_manager = None
        return False
    except Exception as e:
        logger.error(f"❌ Error initializing alerts system: {e}")
        alerts_manager = None
        return False

def validate_multi_subscription_configuration():
    """Validate that all multi-subscription components are properly configured"""
    validation_results = {
        'subscription_manager': False,
        'analysis_engine': False,
        'database_schema': False,
        'background_processor': False,
        'alerts_system': False,
        'cache_system': False
    }
    
    try:
        # Validate subscription manager
        from infrastructure.services.subscription_manager import azure_subscription_manager
        subscriptions = azure_subscription_manager.get_available_subscriptions()
        validation_results['subscription_manager'] = len(subscriptions) > 0
        
        # Validate analysis engine
        validation_results['analysis_engine'] = setup_subscription_aware_analysis_engine()
        
        # Validate database schema
        with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
            validation_results['database_schema'] = cursor.fetchone() is not None
        
        # Validate background processor
        try:
            from infrastructure.services.background_processor import run_subscription_aware_background_analysis
            validation_results['background_processor'] = True
        except ImportError:
            validation_results['background_processor'] = False
        
        # Validate alerts system
        validation_results['alerts_system'] = initialize_subscription_aware_alerts()
        
        # Validate cache system
        validation_results['cache_system'] = analysis_cache.get('subscription_isolation_enabled', False)
        
        # Summary
        total_components = len(validation_results)
        valid_components = sum(1 for valid in validation_results.values() if valid)
        
        logger.info(f"🌐 Multi-subscription validation: {valid_components}/{total_components} components valid")
        
        for component, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            logger.info(f"{status} {component}: {'VALID' if is_valid else 'INVALID'}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"❌ Multi-subscription validation failed: {e}")
        return validation_results

def get_multi_subscription_status():
    """Get comprehensive status of multi-subscription system"""
    try:
        status = {
            'multi_subscription_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Subscription manager status
        try:
            from infrastructure.services.subscription_manager import azure_subscription_manager
            subscriptions = azure_subscription_manager.get_available_subscriptions()
            status['subscriptions'] = {
                'total_count': len(subscriptions),
                'enabled_count': len([s for s in subscriptions if s.state.lower() == 'enabled']),
                'default_subscription': next((s.subscription_id for s in subscriptions if s.is_default), None)
            }
        except Exception as e:
            status['subscriptions'] = {'error': str(e)}
        
        # Database status
        try:
            with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM clusters WHERE subscription_id IS NOT NULL')
                clusters_with_subscription = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT COUNT(DISTINCT subscription_id) FROM clusters WHERE subscription_id IS NOT NULL')
                unique_subscriptions = cursor.fetchone()[0]
                
                status['database'] = {
                    'clusters_with_subscription': clusters_with_subscription,
                    'unique_subscriptions_in_use': unique_subscriptions
                }
        except Exception as e:
            status['database'] = {'error': str(e)}
        
        # Analysis engine status
        try:
            from infrastructure.persistence.processing.analysis_engine import multi_subscription_analysis_engine
            status['analysis_engine'] = {
                'available': True,
                'subscription_locks_count': len(multi_subscription_analysis_engine.subscription_locks)
            }
        except Exception as e:
            status['analysis_engine'] = {'available': False, 'error': str(e)}
        
        # Cache status
        status['cache'] = {
            'subscription_isolation_enabled': analysis_cache.get('subscription_isolation_enabled', False),
            'cached_subscriptions': len(analysis_cache.get('subscriptions', {})),
            'cached_clusters': len(analysis_cache.get('clusters', {}))
        }
        
        # Active sessions
        try:
            active_sessions = enhanced_cluster_manager.get_subscription_analysis_sessions(status='running')
            status['active_analysis_sessions'] = len(active_sessions)
        except Exception as e:
            status['active_analysis_sessions'] = {'error': str(e)}
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Failed to get multi-subscription status: {e}")
        return {'error': str(e), 'multi_subscription_enabled': False}

# Global alerts manager (will be initialized later with subscription support)
alerts_manager = None

# Enhanced startup sequence
def initialize_application_with_multi_subscription():
    """Enhanced application initialization with multi-subscription support"""
    logger.debug("🌐 Initializing multi-subscription AKS cost optimization system")
    
    initialization_steps = [
        ("Database Schema", initialize_database),
        ("Multi-Subscription Environment", initialize_multi_subscription_environment),
        ("Analysis Engine", setup_subscription_aware_analysis_engine),
        ("Alerts System", initialize_subscription_aware_alerts),
    ]
    
    successful_steps = 0
    
    for step_name, step_function in initialization_steps:
        try:
            logger.debug(f"🔄 Initializing {step_name}...")
            success = step_function()
            if success:
                logger.debug(f"✅ {step_name} initialized successfully")
                successful_steps += 1
            else:
                logger.warning(f"⚠️ {step_name} initialization completed with warnings")
                successful_steps += 1  # Still count as successful
        except Exception as e:
            logger.error(f"❌ {step_name} initialization failed: {e}")
    
    # Validate configuration
    validation_results = validate_multi_subscription_configuration()
    
    # Summary
    logger.info(f"🌐 Multi-subscription system ready ({successful_steps}/{len(initialization_steps)} components)")
    
    # Log system status
    status = get_multi_subscription_status()
    if status.get('subscriptions', {}).get('total_count', 0) > 0:
        logger.info(f"🌐 Ready to analyze across {status['subscriptions']['total_count']} Azure subscriptions")
    
    return successful_steps == len(initialization_steps)

# Configuration validation on import - SDK-based
try:
    # Validate Azure SDK is available and working
    from infrastructure.services.azure_sdk_manager import azure_sdk_manager, AZURE_SDK_AVAILABLE
    
    if AZURE_SDK_AVAILABLE and azure_sdk_manager.is_authenticated():
        logger.info("✅ Azure SDK available and authenticated for multi-subscription operations")
    elif AZURE_SDK_AVAILABLE:
        logger.warning("⚠️ Azure SDK available but not authenticated - set Azure credentials")
    else:
        logger.warning("⚠️ Azure SDK not available - subscription operations may fail")
except Exception as e:
    logger.warning(f"⚠️ Could not verify Azure SDK: {e}")

# Export key components
__all__ = [
    'logger',
    'enhanced_cluster_manager',
    'implementation_generator',
    'analysis_cache',
    'analysis_results',
    'analysis_status_tracker',
    '_analysis_sessions',
    '_analysis_lock',
    'initialize_application_with_multi_subscription',
    'get_multi_subscription_status',
    'validate_multi_subscription_configuration',
    'CLUSTER_CONFIG_AVAILABLE',
    'ALERTS_AVAILABLE'
    'alerts_manager'
]