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
    
    # Add performance monitoring for Railway
    try:
        from performance_monitor import add_performance_monitoring
        add_performance_monitoring(app)
        print("✅ Performance monitoring enabled")
    except Exception as e:
        print(f"⚠️ Performance monitoring warning: {e}")
    
    # Start background services for WSGI deployment (delayed for faster startup)
    try:
        # Delay background services to speed up initial startup
        import threading
        import time
        
        def delayed_background_start():
            time.sleep(10)  # Wait 10s after startup
            try:
                from infrastructure.services.auto_analysis_scheduler import auto_scheduler
                auto_scheduler.start_scheduler()
                print("✅ Background services started (delayed)")
            except Exception as e:
                print(f"⚠️ Background services warning: {e}")
        
        # Start background services in separate thread
        background_thread = threading.Thread(target=delayed_background_start, daemon=True)
        background_thread.start()
        print("⏰ Background services scheduled for delayed start")
        
    except Exception as e:
        print(f"⚠️ Background services error: {e}")
    
    print("✅ KubeOpt WSGI application ready")
    return app

# Create the application instance for WSGI servers
app = create_wsgi_app()

if __name__ == "__main__":
    # For direct execution (fallback)
    port = int(os.environ.get("PORT", 5010))
    app.run(host="0.0.0.0", port=port, debug=False)