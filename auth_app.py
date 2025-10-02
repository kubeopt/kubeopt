#!/usr/bin/env python3
"""
Minimal AKS Cost Optimizer with Authentication Only
===================================================

This is a minimal version that starts with just authentication and settings.
Use this to test the login system while the full application dependencies are being resolved.
"""

import os
import sys
from flask import Flask, render_template, redirect, url_for

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def create_minimal_app():
    """Create Flask app with authentication only"""
    
    # Initialize Flask app
    app = Flask(__name__, 
                static_folder='presentation/web/static', 
                template_folder='presentation/web/templates')
    app.secret_key = os.urandom(24)
    
    # Register authentication routes
    from presentation.api.auth_routes import register_auth_routes
    register_auth_routes(app)
    
    # Add a simple dashboard route for testing
    from infrastructure.services.auth_manager import auth_manager
    
    @app.route('/dashboard')
    @auth_manager.require_auth
    def dashboard():
        """Simple dashboard for testing"""
        user = auth_manager.get_current_user()
        return f"""
        <html>
        <head>
            <title>AKS Cost Optimizer - Dashboard</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <nav class="navbar navbar-dark bg-primary">
                <div class="container">
                    <span class="navbar-brand">AKS Cost Optimizer</span>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="/settings">Settings</a>
                        <a class="nav-link" href="/logout">Logout</a>
                    </div>
                </div>
            </nav>
            <div class="container mt-4">
                <div class="alert alert-success">
                    <h4>🎉 Authentication System Working!</h4>
                    <p>Welcome <strong>{user.get('username', 'Admin')}</strong>!</p>
                    <p>Your authentication system is working correctly.</p>
                    <hr>
                    <p class="mb-0">
                        <a href="/settings" class="btn btn-primary">Go to Settings</a>
                        <a href="/logout" class="btn btn-secondary ms-2">Logout</a>
                    </p>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5>System Status</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Username:</strong> {user.get('username', 'Unknown')}</p>
                        <p><strong>Role:</strong> {user.get('role', 'Unknown')}</p>
                        <p><strong>Session Created:</strong> {user.get('created', 'Unknown')}</p>
                        <p><strong>Active Sessions:</strong> {auth_manager.get_active_sessions_count()}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    # Redirect root to dashboard
    @app.route('/')
    def root():
        if auth_manager.validate_session():
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    return app

def main():
    """Main entry point for minimal auth app"""
    print("🚀 Starting AKS Cost Optimizer (Authentication Test Mode)")
    print("=" * 60)
    
    # Create Flask app
    app = create_minimal_app()
    
    print("✅ Authentication system is ready!")
    print("🌐 Access the application at: http://localhost:5002")
    print("🔑 Default credentials: kubeopt / kubeopt")
    print("=" * 60)
    
    # Start the application
    try:
        app.run(host='0.0.0.0', port=5002, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()