"""
FastAPI Application Factory
=============================

KubeOpt v3 — Multi-cloud Kubernetes Cost Optimizer
FastAPI is the sole entry point (Flask removed).
"""

import os
import sys
import logging
import threading
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

# Ensure project root is in sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

_scheduler_ref = None  # Track scheduler for graceful shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    global _scheduler_ref

    # --- Startup ---
    logger.info("KubeOpt FastAPI starting up...")

    # 1. Validate YAML standards (critical — fail fast)
    try:
        from shared.standards.standards_loader import validate_standards_available
        if validate_standards_available():
            logger.info("YAML standards validated successfully")
        else:
            logger.warning("Standards validation returned False — some features may be limited")
    except Exception as e:
        logger.error(f"YAML standards validation FAILED: {e}")
        logger.error("System cannot start without valid standards configuration!")
        raise

    # 2. Multi-subscription initialization
    try:
        from shared.config.config import (
            initialize_application_with_multi_subscription,
            get_multi_subscription_status,
        )
        success = initialize_application_with_multi_subscription()
        if success:
            status = get_multi_subscription_status()
            count = status.get('subscriptions', {}).get('total_count', 0)
            logger.info(f"Multi-subscription init complete: {count} subscriptions available")
        else:
            logger.warning("Multi-subscription init returned False — running with defaults")
    except Exception as e:
        logger.warning(f"Multi-subscription init skipped: {e}")

    # 3. Initialize service container (lazy — services created on first access)
    from presentation.api.v2.services import initialize_container
    container = initialize_container()
    logger.info(f"Cloud provider: {container.cloud_provider}")

    # 4. Start background services (delayed, like Flask wsgi.py pattern)
    def delayed_background_start():
        time.sleep(10)
        try:
            from infrastructure.services.auto_analysis_scheduler import auto_scheduler
            auto_scheduler.start_scheduler()
            global _scheduler_ref
            _scheduler_ref = auto_scheduler
            logger.info("Auto-analysis scheduler started (delayed)")
        except Exception as e:
            logger.warning(f"Auto-analysis scheduler failed to start: {e}")

        try:
            from infrastructure.services.database_cleanup_service import DatabaseCleanupService
            db_cleanup = DatabaseCleanupService()
            db_cleanup.start()
            logger.info("Database cleanup service started (delayed)")
        except Exception as e:
            logger.warning(f"Database cleanup service failed to start: {e}")

    bg_thread = threading.Thread(target=delayed_background_start, daemon=True, name="BackgroundInit")
    bg_thread.start()
    logger.info("Background services scheduled for delayed start")

    logger.info("KubeOpt FastAPI ready")
    yield

    # --- Shutdown ---
    logger.info("KubeOpt FastAPI shutting down...")
    if _scheduler_ref:
        try:
            _scheduler_ref.stop_scheduler()
            logger.info("Auto-analysis scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {e}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not os.getenv('LOCAL_DEV'):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter: 60 requests/minute per IP on /api/* routes."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute
        self._buckets: dict = {}  # ip -> [timestamps]
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path == "/api/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        with self._lock:
            timestamps = self._buckets.get(client_ip, [])
            timestamps = [t for t in timestamps if t > window_start]
            if len(timestamps) >= self.rpm:
                from fastapi.responses import JSONResponse as JR
                retry_after = int(60 - (now - timestamps[0]))
                return JR(
                    status_code=429,
                    content={"error": "Too many requests"},
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            timestamps.append(now)
            self._buckets[client_ip] = timestamps

        return await call_next(request)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="KubeOpt",
        description="Multi-Cloud Kubernetes Cost Optimizer",
        version="3.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Security middleware (outermost — runs first on response)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    # CORS — allow React dev server and production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite dev server
            "http://localhost:5001",   # FastAPI production
            "https://demo.kubeopt.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc) if os.getenv('DEBUG') else None},
        )

    # Register routers
    from presentation.api.v2.routers import (
        health, auth, clusters, analysis, plans,
        kubernetes, settings, subscriptions, scheduler, alerts,
        project_controls, legacy,
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(auth.legacy_router)  # /api/v1/license/* endpoints
    app.include_router(clusters.router)
    app.include_router(analysis.router)
    app.include_router(plans.router)
    app.include_router(kubernetes.router)
    app.include_router(settings.router)
    app.include_router(subscriptions.router)
    app.include_router(scheduler.router)
    app.include_router(alerts.router)
    app.include_router(project_controls.router)
    app.include_router(legacy.router)

    # Serve React SPA static files (only if frontend/dist exists)
    frontend_dist = project_root / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """SPA catch-all — serve static files from dist root, then index.html."""
            from fastapi.responses import FileResponse
            # First check if the path matches a static file in dist root (e.g. images, icons)
            static_file = frontend_dist / full_path
            if full_path and static_file.exists() and static_file.is_file():
                return FileResponse(str(static_file))
            # Otherwise serve SPA index.html
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return JSONResponse(status_code=404, content={"error": "Frontend not built"})

    return app


# Application instance
app = create_app()
