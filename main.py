#!/usr/bin/env python3
"""
AKS Cost Optimizer - Production Entry Point
==========================================
Production-ready version with proper WSGI server support.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer - Clean Architecture Version
"""

import os
import sys
from flask import Flask

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
def load_env_files():
    """Load environment variables from .env files"""
    
    # First load main .env file
    main_env_file = os.path.join(current_dir, '.env')
    if os.path.exists(main_env_file):
        print("🔧 Loading main environment (.env)...")
        with open(main_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Main environment (.env) loaded")
    
    # Then load development overrides if available
    dev_env_file = os.path.join(current_dir, '.env.development')
    if os.path.exists(dev_env_file):
        print("🔧 Loading development environment (.env.development)...")
        with open(dev_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Development environment (.env.development) loaded")

# Load environment variables
load_env_files()

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
    
    # Register license management routes
    from presentation.api.license_routes import register_license_routes
    register_license_routes(app)
    
    # Initialize auto-analysis scheduler
    from infrastructure.services.auto_analysis_scheduler import auto_scheduler
    auto_scheduler.init_app(app)
    
    # Graceful shutdown
    import atexit
    atexit.register(auto_scheduler.stop_scheduler)
    
    return app

def initialize_application():
    """Initialize all application components"""
    
    print("🌐 Initializing AKS Cost Optimizer (Production Mode)")
    
    # CRITICAL: Validate YAML standards before doing anything else
    print("🔍 Validating YAML-based standards configuration...")
    try:
        from shared.standards.standards_loader import validate_standards_available
        validate_standards_available()
        print("✅ YAML standards validation passed")
    except Exception as e:
        print(f"❌ YAML standards validation FAILED: {e}")
        print("🚨 CRITICAL: System cannot start without valid standards configuration!")
        print("   Check that these files exist and are valid:")
        print("   - config/aks_scoring.yaml")
        print("   - config/aks_implementation_standards.yaml")
        return False
    
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
    
    # Start background services after app is created
    from infrastructure.services.auto_analysis_scheduler import auto_scheduler
    try:
        auto_scheduler.start_scheduler()
        print("✅ Auto-analysis scheduler started")
    except Exception as e:
        print(f"⚠️ Auto-analysis scheduler failed to start: {e}")
    
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