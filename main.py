#!/usr/bin/env python3
"""
KubeOpt — Multi-Cloud Kubernetes Cost Optimizer
================================================
Production entry point.  Boots FastAPI via uvicorn.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def load_env_files():
    """Load environment variables from persistent .env file."""
    settings_dir = os.getenv('SETTINGS_PATH', current_dir)
    main_env_file = os.path.join(settings_dir, '.env')

    if os.path.exists(main_env_file):
        print(f"Loading environment variables from {main_env_file}...")
        with open(main_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    os.environ[key] = value
        print("Environment variables loaded")
    else:
        print(f"No .env file found at {main_env_file}")


# Load environment variables at import time
load_env_files()


def main():
    """Main application entry point — starts uvicorn."""
    import uvicorn

    print("Starting KubeOpt (FastAPI)")
    print("=" * 60)

    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')

    print(f"Server: uvicorn on {host}:{port}")
    print(f"Docs:   http://localhost:{port}/docs")
    print("=" * 60)

    try:
        uvicorn.run(
            "fastapi_app:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Application error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
