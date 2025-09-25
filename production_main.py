#!/usr/bin/env python3
"""
AKS Cost Optimizer - Production Entry Point
==========================================
Production-ready version with proper WSGI server support.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer - Clean Architecture Version
"""

import os
import sys
from flask import Flask

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def create_app():
    """
    Application factory for creating Flask app with clean architecture
    """
    
    # Initialize Flask app
    app = Flask(__name__, 
                static_folder='presentation/web/static', 
                template_folder='presentation/web/templates')
    app.secret_key = os.urandom(24)
    
    # Register authentication routes first
    from presentation.api.auth_routes import register_auth_routes
    register_auth_routes(app)
    
    # Register routes using clean architecture
    from presentation.api.routes import register_routes
    register_routes(app)
    
    # Register API routes (contains most of the endpoints)
    from presentation.api.api_routes import register_api_routes
    register_api_routes(app)
    
    return app

def initialize_application():
    """Initialize all application components"""
    
    print("🌐 Initializing AKS Cost Optimizer (Production Mode)")
    
    # Initialize configuration
    from shared.config.config import (
        initialize_application_with_multi_subscription,
        get_multi_subscription_status
    )
    
    # Initialize the application
    success = initialize_application_with_multi_subscription()
    
    if success:
        print("✅ Application initialization completed successfully")
        
        # Log system status
        status = get_multi_subscription_status()
        subscriptions_count = status.get('subscriptions', {}).get('total_count', 0)
        print(f"🌐 System Status: {subscriptions_count} subscriptions available")
        
        return True
    else:
        print("❌ Application initialization failed")
        return False

def main():
    """Main application entry point for production"""
    
    print("🚀 Starting AKS Cost Optimizer (Production Mode)")
    print("=" * 60)
    
    # Initialize application components
    if not initialize_application():
        print("❌ Failed to initialize application. Exiting.")
        return False
    
    # Create Flask app
    app = create_app()
    
    print("=" * 60)
    print("✅ AKS Cost Optimizer is ready!")
    print("🌐 Access the application at: http://localhost:5001")
    print("📊 Enterprise metrics: http://localhost:5001/api/enterprise-metrics")
    print("=" * 60)
    
    # Production server options
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Start the application (production mode - no debug)
    try:
        print(f"🌟 Starting production server on {host}:{port}")
        app.run(host=host, port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        return False
    
    return True

# For WSGI servers (Gunicorn, uWSGI, etc.)
app = None
if __name__ != "__main__":
    # Initialize for WSGI
    if initialize_application():
        app = create_app()

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)