#!/usr/bin/env python3
"""
AKS Cost Optimizer - Run on Port 5001
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Add project root to Python path"""
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root

def main():
    print("🚀 AKS Cost Optimizer - Starting on Port 5001")
    print("=" * 60)
    
    # Setup Python path
    project_root = setup_python_path()
    print(f"📁 Project root: {project_root}")
    
    # Change to project directory
    os.chdir(project_root)
    
    try:
        print("📦 Importing Flask app...")
        
        # Import the Flask app
        from app.main.app import app
        
        print("✅ Flask app imported successfully!")
        print("🌐 Starting development server on PORT 5001...")
        print("📱 Open your browser to: http://localhost:5001")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the Flask development server on port 5001
        app.run(
            host="0.0.0.0",
            port=5001,  # Using port 5001 instead of 5000
            debug=True,
            use_reloader=True
        )
        
    except Exception as e:
        print(f"❌ Application Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()