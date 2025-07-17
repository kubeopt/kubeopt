# app/alerts/__init__.py - Fixed alerts module initialization

"""
AKS Cost Intelligence Alerts Module
Provides alerts functionality with proper imports and error handling
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global variables
_alerts_manager = None
ALERTS_AVAILABLE = False

def initialize_alerts_system(cluster_manager=None):
    """Initialize the alerts system"""
    global _alerts_manager, ALERTS_AVAILABLE
    
    try:
        from .enhanced_alerts_manager import init_enhanced_alerts_service
        
        _alerts_manager = init_enhanced_alerts_service(cluster_manager)
        ALERTS_AVAILABLE = _alerts_manager is not None
        
        if ALERTS_AVAILABLE:
            logger.info("✅ Alerts system initialized successfully")
        else:
            logger.error("❌ Failed to initialize alerts system")
            
        return _alerts_manager
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize alerts system: {e}")
        ALERTS_AVAILABLE = False
        return None

def register_alerts_routes(app):
    """Register alerts routes with the Flask app"""
    try:
        if not ALERTS_AVAILABLE or not _alerts_manager:
            logger.warning("⚠️ Alerts system not available, skipping route registration")
            return
        
        @app.route('/api/alerts', methods=['GET'])
        def get_alerts():
            """Get all alerts"""
            return _alerts_manager.get_alerts_route()
        
        @app.route('/api/alerts', methods=['POST'])
        def create_alert():
            """Create new alert"""
            from flask import request
            return _alerts_manager.create_alert_route(request.json)
        
        @app.route('/api/alerts/<int:alert_id>', methods=['PUT'])
        def update_alert(alert_id):
            """Update alert"""
            from flask import request
            return _alerts_manager.update_alert_route(alert_id, request.json)
        
        @app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
        def delete_alert(alert_id):
            """Delete alert"""
            return _alerts_manager.delete_alert_route(alert_id)
        
        @app.route('/api/alerts/<int:alert_id>/test', methods=['POST'])
        def test_alert(alert_id):
            """Test alert notifications"""
            return _alerts_manager.test_alert_route(alert_id)
        
        @app.route('/api/alerts/triggers', methods=['GET'])
        @app.route('/api/alerts/<int:alert_id>/triggers', methods=['GET'])
        def get_alert_triggers(alert_id=None):
            """Get alert triggers"""
            return _alerts_manager.get_alert_triggers_route(alert_id)
        
        @app.route('/api/alerts/statistics', methods=['GET'])
        def get_alert_statistics():
            """Get alert statistics"""
            return _alerts_manager.get_alert_statistics_route()
        
        logger.info("✅ Alerts routes registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register alerts routes: {e}")

def check_alerts_after_analysis(cluster_id: str, analysis_results: Dict[str, Any]):
    """Check and trigger alerts after cost analysis"""
    try:
        if not ALERTS_AVAILABLE or not _alerts_manager:
            logger.debug("⚠️ Alerts system not available for checking")
            return []
        
        # Extract current cost from analysis results
        current_cost = 0.0
        if 'total_cost' in analysis_results:
            current_cost = float(analysis_results['total_cost'])
        elif 'cost_breakdown' in analysis_results:
            cost_breakdown = analysis_results['cost_breakdown']
            if isinstance(cost_breakdown, dict) and 'total' in cost_breakdown:
                current_cost = float(cost_breakdown['total'])
        
        if current_cost > 0:
            triggered_alerts = _alerts_manager.check_cluster_alerts(cluster_id, current_cost)
            if triggered_alerts:
                logger.info(f"🚨 Triggered {len(triggered_alerts)} alerts for cluster {cluster_id}")
            return triggered_alerts
        else:
            logger.debug(f"⚠️ No valid cost data found for cluster {cluster_id}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error checking alerts for cluster {cluster_id}: {e}")
        return []

def get_alerts_manager():
    """Get the alerts manager instance"""
    return _alerts_manager

def is_alerts_available() -> bool:
    """Check if alerts system is available"""
    return ALERTS_AVAILABLE

def shutdown_alerts_system():
    """Shutdown the alerts system"""
    global _alerts_manager, ALERTS_AVAILABLE
    
    try:
        if _alerts_manager:
            from .enhanced_alerts_manager import shutdown_enhanced_alerts_service
            shutdown_enhanced_alerts_service()
            
        _alerts_manager = None
        ALERTS_AVAILABLE = False
        logger.info("✅ Alerts system shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during alerts system shutdown: {e}")

# Module exports
__all__ = [
    'ALERTS_AVAILABLE',
    'initialize_alerts_system',
    'register_alerts_routes', 
    'check_alerts_after_analysis',
    'get_alerts_manager',
    'is_alerts_available',
    'shutdown_alerts_system'
]

logger.info("✅ Alerts module loaded successfully")