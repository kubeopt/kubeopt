"""
AKS Cost Optimization Tool - MULTI-SUBSCRIPTION MAIN APPLICATION ENTRY POINT
---------------------------------------------------------------------------
Enhanced main application with comprehensive multi-subscription support,
parallel analysis capabilities, and subscription-aware cost optimization.
"""

import os
import sys
import signal
from flask import Flask

# Add the app directory to Python path for imports
app_dir = os.path.dirname(__file__)
sys.path.insert(0, app_dir)

# UPDATED IMPORTS - use the enhanced multi-subscription configuration
from config import (
    logger, enhanced_cluster_manager, analysis_cache, 
    initialize_application_with_multi_subscription, 
    get_multi_subscription_status,
    implementation_generator,
    analysis_results
)

# Initialize Flask app with enhanced configuration
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
app.secret_key = os.urandom(24)

def initialize_multi_subscription_application():
    """Initialize all multi-subscription application components"""
    try:
        logger.info("🌐 Initializing Multi-Subscription AKS Cost Optimization Tool")
        
        # Use the enhanced initialization function
        success = initialize_application_with_multi_subscription()
        
        if success:
            logger.info("✅ Multi-subscription application initialization completed successfully")
            
            # Log system status
            status = get_multi_subscription_status()
            logger.info(f"🌐 System Status: {status.get('subscriptions', {}).get('total_count', 0)} subscriptions available")
            
            return True
        else:
            logger.error("❌ Multi-subscription application initialization failed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Multi-subscription application initialization failed: {e}")
        return False

def register_all_routes_with_multi_subscription():
    """Register all application routes with multi-subscription support"""
    try:
        logger.info("🛣️ Registering multi-subscription application routes...")
        
        # Register enhanced main routes (portfolio, dashboard) with subscription support
        from app.interface.routes import register_routes
        register_routes(app)
        
        # Register enhanced API routes with subscription awareness
        from app.interface.api_routes import register_api_routes
        register_api_routes(app)
        
        # FIXED: Register alerts routes (subscription-aware) 
        try:
            from app.alerts import register_alerts_routes
            register_alerts_routes(app)
            logger.info("✅ Alerts routes registered successfully")
        except ImportError as import_error:
            logger.warning(f"⚠️ Alerts routes not available: {import_error}")
        except Exception as alerts_error:
            logger.error(f"❌ Failed to register alerts routes: {alerts_error}")
        
        # Register enhanced utility routes
        register_enhanced_utility_routes()
        
        logger.info("✅ All multi-subscription routes registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-subscription route registration failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def register_enhanced_utility_routes():
    """Register enhanced utility routes with multi-subscription support"""
    
    @app.route('/')
    def index():
        """Default route - redirect to cluster portfolio"""
        from flask import redirect, url_for
        try:
            return redirect(url_for('cluster_portfolio'))
        except Exception as e:
            logger.error(f"Failed to redirect to cluster_portfolio: {e}")
            # Fallback to direct redirect
            return redirect('/cluster-portfolio')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        from flask import jsonify
        return jsonify({'status': 'healthy', 'service': 'aks-optimizer'}), 200
    
    @app.route('/multi-subscription-status')
    def multi_subscription_status():
        """Multi-subscription system status interface"""
        from flask import jsonify
        try:
            status = get_multi_subscription_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e), 'multi_subscription_enabled': False}), 500

    @app.route('/subscription-management')
    def subscription_management_interface():
        """Subscription management interface"""
        return app.send_static_file('subscription_management.html')

    @app.route('/database-management')
    def database_management():
        """Enhanced database and cache management interface"""
        return app.send_static_file('database_cache_management.html')

    @app.route('/api/subscriptions/health', methods=['GET'])
    def api_subscription_health():
        """Get health status of all subscriptions"""
        try:
            from flask import jsonify
            from app.services.background_processor import monitor_subscription_analysis_health
            
            health_data = monitor_subscription_analysis_health()
            return jsonify({
                'status': 'success',
                'health_data': health_data,
                'multi_subscription_enabled': True
            })
            
        except Exception as e:
            logger.error(f"❌ Subscription health check failed: {e}")
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/cache/subscription-status', methods=['GET'])
    def cache_subscription_status():
        """Get detailed cache status with subscription breakdown"""
        try:
            from flask import request, jsonify
            from datetime import datetime
            from services.cache_manager import is_cache_valid
            
            subscription_id = request.args.get('subscription_id')
            
            status_info = {
                'total_cached_clusters': len(analysis_cache['clusters']),
                'cached_subscriptions': len(analysis_cache.get('subscriptions', {})),
                'subscription_isolation_enabled': analysis_cache.get('subscription_isolation_enabled', False),
                'global_ttl_hours': analysis_cache['global_ttl_hours'],
                'cache_type': 'multi_subscription'
            }
            
            if subscription_id:
                # Specific subscription status
                subscription_clusters = [
                    cluster_id for cluster_id, cache_data in analysis_cache['clusters'].items()
                    if cache_data.get('data', {}).get('subscription_metadata', {}).get('subscription_id') == subscription_id
                ]
                
                status_info.update({
                    'subscription_id': subscription_id,
                    'subscription_clusters': subscription_clusters,
                    'subscription_cluster_count': len(subscription_clusters)
                })
                
                # Add details for each cluster in this subscription
                for cluster_id in subscription_clusters:
                    cluster_cache = analysis_cache['clusters'][cluster_id]
                    status_info[f'cluster_{cluster_id}'] = {
                        'cache_valid': is_cache_valid(cluster_id),
                        'cache_timestamp': cluster_cache.get('timestamp'),
                        'total_cost': cluster_cache.get('data', {}).get('total_cost', 0)
                    }
            else:
                # All subscriptions summary
                subscription_summaries = {}
                for sub_id, sub_data in analysis_cache.get('subscriptions', {}).items():
                    subscription_summaries[sub_id] = {
                        'subscription_name': sub_data.get('subscription_name', 'Unknown'),
                        'cluster_count': len(sub_data.get('clusters', [])),
                        'last_updated': sub_data.get('last_updated')
                    }
                
                status_info['subscription_summaries'] = subscription_summaries
            
            return jsonify({
                'status': 'success',
                'cache_status': status_info,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Enhanced analysis sessions monitoring with subscription awareness
    @app.route('/api/analysis-sessions/subscription', methods=['GET'])
    def get_subscription_analysis_sessions():
        """Monitor subscription-aware analysis sessions"""
        try:
            from flask import request, jsonify
            
            subscription_id = request.args.get('subscription_id')
            status = request.args.get('status')
            
            sessions = enhanced_cluster_manager.get_subscription_analysis_sessions(
                subscription_id=subscription_id,
                status=status
            )
            
            return jsonify({
                'status': 'success',
                'sessions': sessions,
                'total_sessions': len(sessions),
                'subscription_id': subscription_id,
                'filter_status': status
            })
            
        except Exception as e:
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Batch analysis management
    @app.route('/api/analysis/batch', methods=['POST'])
    def api_batch_analysis():
        """Trigger batch analysis across multiple subscriptions"""
        try:
            from flask import request, jsonify
            from app.services.background_processor import run_batch_subscription_analysis
            import threading
            
            data = request.get_json() or {}
            cluster_configs = data.get('clusters', [])
            max_concurrent = data.get('max_concurrent', 3)
            
            if not cluster_configs:
                return jsonify({
                    'status': 'error',
                    'message': 'No cluster configurations provided'
                }), 400
            
            # Validate cluster configurations
            for config in cluster_configs:
                required_fields = ['cluster_id', 'resource_group', 'cluster_name']
                if not all(field in config for field in required_fields):
                    return jsonify({
                        'status': 'error',
                        'message': f'Missing required fields in cluster config: {required_fields}'
                    }), 400
            
            # Start batch analysis in background
            batch_thread = threading.Thread(
                target=run_batch_subscription_analysis,
                args=(cluster_configs, max_concurrent),
                daemon=True
            )
            batch_thread.start()
            
            return jsonify({
                'status': 'success',
                'message': f'Batch analysis started for {len(cluster_configs)} clusters',
                'cluster_count': len(cluster_configs),
                'max_concurrent': max_concurrent
            })
            
        except Exception as e:
            logger.error(f"❌ Batch analysis API error: {e}")
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Performance metrics
    @app.route('/api/subscriptions/<subscription_id>/metrics', methods=['GET'])
    def get_subscription_metrics(subscription_id: str):
        """Get performance metrics for specific subscription"""
        try:
            from flask import request, jsonify
            
            hours_back = request.args.get('hours_back', 24, type=int)
            
            metrics = enhanced_cluster_manager.get_subscription_performance_metrics(
                subscription_id, hours_back
            )
            
            return jsonify({
                'status': 'success',
                'subscription_id': subscription_id,
                'metrics': metrics,
                'hours_back': hours_back
            })
            
        except Exception as e:
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

def clear_global_analysis_cache():
    """Clear global analysis cache to prevent cross-cluster contamination"""
    global analysis_results
    analysis_results.clear()
    logger.info("🧹 Cleared global analysis cache for multi-subscription isolation")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully for multi-subscription system"""
    logger.info("👋 Shutting down multi-subscription system gracefully...")
    
    # Stop alerts manager
    try:
        from config import alerts_manager
        if alerts_manager:
            alerts_manager.stop_service()
    except Exception as e:
        logger.warning(f"⚠️ Alerts shutdown warning: {e}")
    
    # Clean up any active subscription analysis sessions
    try:
        enhanced_cluster_manager.cleanup_stale_subscription_sessions(max_age_hours=0)
        logger.info("🧹 Cleaned up active subscription analysis sessions")
    except Exception as e:
        logger.warning(f"⚠️ Session cleanup warning: {e}")
    
    logger.info("✅ Multi-subscription system shutdown complete")
    sys.exit(0)

# CRITICAL FIX: Initialize and register routes when module is imported
# This ensures routes are available when Flask starts with 'flask run'
try:
    logger.info("🚀 Initializing application on module import...")
    
    # Initialize application
    if initialize_multi_subscription_application():
        logger.info("✅ Application components initialized")
        
        # Register all routes
        if register_all_routes_with_multi_subscription():
            logger.info("✅ Routes registered successfully")
        else:
            logger.error("❌ Failed to register routes")
    else:
        logger.error("❌ Failed to initialize application")
        
except Exception as e:
    logger.error(f"❌ Failed to initialize on import: {e}")
    import traceback
    logger.error(traceback.format_exc())

def main():
    """Main application entry point with multi-subscription support"""
    try:
        logger.info("=" * 80)
        logger.info("🌐 STARTING MULTI-SUBSCRIPTION AKS COST OPTIMIZATION TOOL")
        logger.info("=" * 80)
        
        # Application should already be initialized from module import
        # Just log the status
        status = get_multi_subscription_status()
        if status.get('subscriptions', {}).get('total_count', 0) > 0:
            sub_count = status['subscriptions']['total_count']
            enabled_count = status['subscriptions']['enabled_count']
            logger.info(f"🌐 Ready to analyze {enabled_count}/{sub_count} Azure subscriptions")
        
        logger.info("🌐 Server ready at http://127.0.0.1:5000/")
        logger.info("💡 Press Ctrl+C to exit")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the Flask application
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
        return True
        
    except KeyboardInterrupt:
        logger.info("👋 Multi-subscription application shutdown requested by user")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-subscription application startup failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

# IMPLEMENTATION INSTRUCTIONS
"""
MULTI-SUBSCRIPTION AKS COST OPTIMIZATION - IMPLEMENTATION GUIDE
============================================================

This implementation provides comprehensive multi-subscription support for your AKS cost optimization tool.
Here's what has been implemented and how to deploy it:

## KEY FEATURES IMPLEMENTED:

1. **Multi-Subscription Analysis**
   - Automatic subscription detection and validation
   - Parallel analysis across multiple Azure subscriptions
   - Subscription-aware cost data collection and processing
   - Session-based analysis tracking with subscription context

2. **Enhanced UI with Subscription Support**
   - Subscription dropdown in cluster addition form
   - Subscription grouping in cluster portfolio view
   - Analysis tab removed (as requested) - analysis now via cluster cards only
   - Default 30-day analysis (as requested)
   - Subscription context display in dashboards

3. **Database Enhancements**
   - Multi-subscription schema with proper foreign keys
   - Subscription tracking and performance metrics
   - Analysis session management per subscription
   - Automated migration from existing single-subscription setup

4. **Parallel Analysis Capabilities**
   - Thread-safe subscription-specific analysis
   - Per-subscription locking to prevent conflicts
   - Concurrent analysis across different subscriptions
   - Background processing with subscription awareness

5. **Azure CLI Integration**
   - Automatic subscription discovery
   - Subscription context switching for analysis
   - Cluster validation within subscription context
   - Subscription health monitoring

## DEPLOYMENT STEPS:

### 1. Prerequisites
```bash
# Ensure Azure CLI is installed and logged in
az login
az account list --output table

# Verify you have access to multiple subscriptions
az account list --query "[].{Name:name, SubscriptionId:id, State:state}" --output table
```

### 2. File Replacement
Replace your existing files with the provided implementations:

```
app/services/subscription_manager.py (NEW)
app/data/processing/multi_subscription_analysis_engine.py (ENHANCED)
app/interface/api_routes.py (UPDATED)
app/interface/routes.py (UPDATED)
app/data/cluster_database.py (ENHANCED)
app/services/background_processor.py (UPDATED)
app/main/config.py (UPDATED)
app/main/main.py (UPDATED)
frontend/templates/cluster_portfolio.html (ENHANCED)
frontend/templates/unified_dashboard.html (UPDATED - ANALYSIS TAB REMOVED)
```

### 3. Database Migration
The system will automatically migrate your existing database to support multiple subscriptions:

```python
# The migration will:
# - Add subscription_id and subscription_name columns to clusters table
# - Create subscriptions table for tracking available subscriptions  
# - Create subscription_analysis_sessions table for session tracking
# - Create subscription_performance table for metrics
# - Automatically detect and update subscription info for existing clusters
```

### 4. Configuration
No additional configuration needed! The system will:
- Auto-discover your available Azure subscriptions
- Validate cluster access across subscriptions
- Set up subscription-aware caching and analysis

### 5. Testing Multi-Subscription Features

1. **Add a cluster from any subscription:**
   - Go to cluster portfolio
   - Click "Add Cluster" 
   - Select subscription from dropdown
   - Enter cluster details
   - System validates access automatically

2. **Run analysis on any cluster:**
   - Click "Analyze" button on any cluster card
   - System automatically detects and uses correct subscription
   - Analysis runs with 30-day default (analysis tab removed as requested)
   - Progress tracked with subscription context

3. **View multi-subscription portfolio:**
   - Clusters grouped by subscription
   - Subscription health indicators
   - Cross-subscription cost summaries

## API ENHANCEMENTS:

New endpoints for multi-subscription support:
- GET /api/subscriptions - List available subscriptions
- POST /api/subscriptions/{id}/validate - Validate cluster access
- GET /api/subscriptions/health - Subscription health check
- POST /api/analysis/batch - Batch analysis across subscriptions
- GET /api/analysis-sessions/subscription - Subscription-aware session monitoring

## SUBSCRIPTION ISOLATION:

- Each analysis runs in subscription-specific context
- Thread-safe subscription switching
- Isolated caching per subscription  
- No cross-subscription data contamination
- Parallel analysis across different subscriptions

## PERFORMANCE OPTIMIZATIONS:

- Concurrent analysis with configurable limits
- Subscription-specific locking for thread safety
- Efficient caching with subscription isolation
- Background maintenance for session cleanup
- Performance metrics tracking per subscription

## BACKWARD COMPATIBILITY:

All existing functionality preserved:
- Existing clusters automatically get subscription context
- Original APIs still work with auto-detection
- Gradual migration of existing data
- Fallback to single-subscription mode if needed

## MONITORING & TROUBLESHOOTING:

Enhanced logging with subscription context:
- Session-based tracking with subscription IDs
- Performance metrics per subscription
- Health monitoring for subscription access
- Detailed error reporting with subscription context

The system is production-ready and handles:
- Azure CLI authentication across subscriptions
- Automatic subscription discovery and validation
- Graceful handling of subscription access issues
- Session timeout and cleanup
- Concurrent analysis limits and resource management

Start the application and enjoy multi-subscription AKS cost optimization! 🌐
"""