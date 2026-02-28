#!/usr/bin/env python3
"""
WSGI / ASGI Entry Point for Production Deployment
==================================================
Exports the FastAPI application for gunicorn + uvicorn workers.

Usage:
    gunicorn wsgi:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5001
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables before importing the app
from main import load_env_files
load_env_files()

# Import the FastAPI application instance
from fastapi_app import app  # noqa: E402, F401

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=port, log_level="info")
