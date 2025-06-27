"""
AKS Cost Optimization Tool - Main Application Entry Point
---------------------------------------------------------
A web application for analyzing and optimizing AKS costs, with a focus on
memory-based HPA implementation and generalizable metrics collection.
"""

import os
import sys
from flask import Flask

# Add the app directory to Python path for imports
app_dir = os.path.dirname(__file__)
sys.path.insert(0, app_dir)

# Import from the organized folder structure
from config import (
    logger, enhanced_cluster_manager, analysis_cache, 
    initialize_database, implementation_generator,
    analysis_results
)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
app.secret_key = os.urandom(24)

def initialize_application():
    """Initialize all application components"""
    try:
        logger.info("🚀 Initializing AKS Cost Optimization Tool")
        
        # Initialize database first
        logger.info("📊 Initializing database...")
        initialize_database()
        
        # Initialize alerts system
        logger.info("🔔 Initializing alerts system...")
        from app.services.alerts_integration import initialize_alerts_system
        alerts_manager = initialize_alerts_system()
        
        # Initialize database management
        try:
            from app.data.database_management import init_database_management, db_mgmt_bp
            init_database_management(enhanced_cluster_manager, alerts_manager, analysis_cache)
            # Register database management blueprint
            app.register_blueprint(db_mgmt_bp)
            logger.info("✅ Database management initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Database management module not available: {e}")
        
        logger.info("✅ Application initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Application initialization failed: {e}")
        return False

def register_all_routes():
    """Register all application routes"""
    try:
        logger.info("🛣️ Registering application routes...")
        
        # Register main routes (dashboard, portfolio)
        from app.interface.routes import register_routes
        register_routes(app)
        
        # Register API routes (with unique function names)
        from app.interface.api_routes import register_api_routes
        register_api_routes(app)
        
        # Register alerts routes
        from services.alerts_integration import register_alerts_routes
        register_alerts_routes(app)
        
        # Additional utility routes
        register_utility_routes()
        
        logger.info("✅ All routes registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Route registration failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def register_utility_routes():
    """Register additional utility routes"""
    
    @app.route('/cache-management')
    def cache_management():
        """Cache management interface"""
        return app.send_static_file('cache_management.html')

    @app.route('/database-management')
    def database_management():
        """Database and cache management interface"""
        return app.send_static_file('database_cache_management.html')

    @app.route('/api/cache/status', methods=['GET'])
    def cache_status():
        """Get detailed cache status for debugging"""
        try:
            from flask import request, jsonify
            from datetime import datetime
            from services.cache_manager import is_cache_valid
            
            cluster_id = request.args.get('cluster_id')
            
            status_info = {
                'total_cached_clusters': len(analysis_cache['clusters']),
                'cached_clusters': list(analysis_cache['clusters'].keys()),
                'global_ttl_hours': analysis_cache['global_ttl_hours'],
                'cache_type': 'multi_cluster'
            }
            
            if cluster_id:
                # Specific cluster status
                if cluster_id in analysis_cache['clusters']:
                    cluster_cache = analysis_cache['clusters'][cluster_id]
                    status_info.update({
                        'cluster_id': cluster_id,
                        'cache_valid': is_cache_valid(cluster_id),
                        'cache_timestamp': cluster_cache.get('timestamp'),
                        'cache_has_data': bool(cluster_cache.get('data')),
                        'cache_total_cost': cluster_cache.get('data', {}).get('total_cost', 0),
                        'cache_has_pod_costs': cluster_cache.get('data', {}).get('has_pod_costs', False),
                        'namespace_count_in_cache': len(cluster_cache.get('data', {}).get('namespace_costs', {}))
                    })
                else:
                    status_info.update({
                        'cluster_id': cluster_id,
                        'cache_exists': False,
                        'message': f'No cache found for cluster {cluster_id}'
                    })
            else:
                # All clusters summary
                cluster_summaries = {}
                for cid, cache_data in analysis_cache['clusters'].items():
                    cluster_summaries[cid] = {
                        'cost': cache_data.get('data', {}).get('total_cost', 0),
                        'timestamp': cache_data.get('timestamp'),
                        'valid': is_cache_valid(cid)
                    }
                status_info['cluster_summaries'] = cluster_summaries
            
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

    # Analysis sessions monitoring
    @app.route('/api/analysis-sessions', methods=['GET'])
    def get_analysis_sessions():
        """Monitor active analysis sessions"""
        try:
            from flask import jsonify
            from main.config import _analysis_lock, _analysis_sessions
            
            with _analysis_lock:
                sessions = {
                    sid: {
                        'cluster_id': sdata['cluster_id'],
                        'status': sdata['status'],
                        'started_at': sdata['started_at'],
                        'thread_id': sdata['thread_id']
                    } for sid, sdata in _analysis_sessions.items()
                }
            
            return jsonify({
                'status': 'success',
                'active_sessions': len(sessions),
                'sessions': sessions
            })
        except Exception as e:
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Batch analysis status
    @app.route('/api/analysis-status/batch', methods=['POST'])
    def get_batch_analysis_status():
        """Get analysis status for multiple clusters"""
        try:
            from flask import request, jsonify
            from main.config import analysis_status_tracker
            import sqlite3
            
            request_data = request.get_json() or {}
            cluster_ids = request_data.get('cluster_ids', [])
            
            if not cluster_ids:
                return jsonify({
                    'status': 'error',
                    'message': 'No cluster IDs provided'
                }), 400
            
            statuses = []
            
            for cluster_id in cluster_ids:
                # Check in-memory tracker first
                if cluster_id in analysis_status_tracker:
                    statuses.append({
                        'cluster_id': cluster_id,
                        **analysis_status_tracker[cluster_id]
                    })
                else:
                    # Check database
                    with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.execute('''
                            SELECT analysis_status, analysis_progress, analysis_message
                            FROM clusters WHERE id = ?
                        ''', (cluster_id,))
                        
                        row = cursor.fetchone()
                        if row:
                            statuses.append({
                                'cluster_id': cluster_id,
                                'status': row['analysis_status'] or 'pending',
                                'progress': row['analysis_progress'] or 0,
                                'message': row['analysis_message'] or 'Ready for analysis'
                            })
            
            return jsonify({
                'status': 'success',
                'statuses': statuses
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting batch analysis status: {e}")
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Clusters overview
    @app.route('/api/clusters/overview', methods=['GET'])
    def get_clusters_overview():
        """Get portfolio overview with analysis status counts"""
        try:
            from flask import jsonify
            import sqlite3
            
            with sqlite3.connect(enhanced_cluster_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get overview counts
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN analysis_status = 'analyzing' THEN 1 ELSE 0 END) as analyzing,
                        SUM(CASE WHEN analysis_status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN analysis_status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN analysis_status = 'pending' OR analysis_status IS NULL THEN 1 ELSE 0 END) as pending
                    FROM clusters 
                    WHERE status = 'active'
                ''')
                
                row = cursor.fetchone()
                overview = dict(row) if row else {}
                
                return jsonify({
                    'status': 'success',
                    'overview': overview
                })
                
        except Exception as e:
            logger.error(f"❌ Error getting clusters overview: {e}")
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Maintenance routes
    @app.route('/api/maintenance/cleanup', methods=['POST'])
    def api_cleanup_database():
        """API endpoint to cleanup old analysis data"""
        try:
            from flask import request, jsonify
            
            days_to_keep = request.json.get('days_to_keep', 90) if request.is_json else 90
            
            enhanced_cluster_manager.cleanup_old_analyses(days_to_keep)
            
            return jsonify({
                'status': 'success',
                'message': f'Cleaned up analysis data older than {days_to_keep} days'
            })
            
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    @app.route('/api/clusters/<cluster_id>/history')
    def api_cluster_analysis_history(cluster_id: str):
        """API to get analysis history for a cluster"""
        try:
            from flask import request, jsonify
            
            limit = request.args.get('limit', 10, type=int)
            history = enhanced_cluster_manager.get_analysis_history(cluster_id, limit)
            
            return jsonify({
                'status': 'success',
                'cluster_id': cluster_id,
                'history': history,
                'total_analyses': len(history)
            })
            
        except Exception as e:
            logger.error(f"❌ Error getting analysis history: {e}")
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

def clear_global_analysis_cache():
    """Clear global analysis cache to prevent cross-cluster contamination"""
    global analysis_results
    analysis_results.clear()
    logger.info("🧹 Cleared global analysis cache")

import signal
import sys

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("👋 Shutting down gracefully...")
    
    # Stop alerts manager
    try:
        from config import alerts_manager
        if alerts_manager:
            alerts_manager.stop_service()
    except Exception as e:
        logger.warning(f"⚠️ Alerts shutdown warning: {e}")
    
    logger.info("✅ Shutdown complete")
    sys.exit(0)


def main():
    """Main application entry point"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 Starting AKS Cost Optimization Tool")
        logger.info("=" * 60)
        
        # Initialize application components
        if not initialize_application():
            logger.error("❌ Application initialization failed")
            return False
        
        # Register all routes
        if not register_all_routes():
            logger.error("❌ Route registration failed")
            return False
        
        # Application ready
        logger.info("✅ Application initialization completed successfully")
        logger.info("📊 Multi-cluster portfolio management enabled")
        logger.info("🤖 ML-enhanced analysis engine ready")
        logger.info("🔔 Alerts system initialized")
        logger.info("💾 Cache management system active")
        logger.info("🌐 Server ready at http://127.0.0.1:5000/")
        logger.info("💡 Press Ctrl+C to exit")
        
        # Start the Flask application
        app.run(debug=True, use_reloader=False)
        
        return True
        
    except KeyboardInterrupt:
        logger.info("👋 Application shutdown requested by user")
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        return True
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)