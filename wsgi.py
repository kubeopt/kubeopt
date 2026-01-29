#!/usr/bin/env python3
"""
WSGI Entry Point for Railway Deployment
======================================
Production WSGI entry point for KubeOpt deployment on Railway.

This file provides a proper WSGI application instance that can be used
by gunicorn and other WSGI servers.
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables first
def load_env_files():
    """Load environment variables from persistent .env file"""
    main_env_file = os.path.join(current_dir, '.env')
    if os.path.exists(main_env_file):
        print(f"🔧 Loading environment variables from {main_env_file}...")
        with open(main_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    os.environ[key] = value
        print("✅ Environment variables loaded")

# Load environment first
load_env_files()

# Initialize application for WSGI
def create_wsgi_app():
    """Create and initialize the WSGI application"""
    print("🚀 Initializing KubeOpt for WSGI deployment...")
    
    # Import and run initialization
    from main import initialize_application, create_app
    
    # Initialize application components
    if not initialize_application():
        print("❌ Failed to initialize application")
        raise RuntimeError("Application initialization failed")
    
    # Create Flask app
    app = create_app()
    
    # Start background services for WSGI deployment
    try:
        from infrastructure.services.auto_analysis_scheduler import auto_scheduler
        auto_scheduler.start_scheduler()
        print("✅ Background services started for WSGI")
    except Exception as e:
        print(f"⚠️ Background services warning: {e}")
    
    print("✅ KubeOpt WSGI application ready")
    return app

# Create the application instance for WSGI servers
app = create_wsgi_app()

if __name__ == "__main__":
    # For direct execution (fallback)
    port = int(os.environ.get("PORT", 5010))
    app.run(host="0.0.0.0", port=port, debug=False)