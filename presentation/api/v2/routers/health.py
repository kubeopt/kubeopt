"""Health check endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from presentation.api.v2.dependencies.services import get_provider_registry, get_cloud_provider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/api/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "kubeopt",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
    }


@router.get("/api/system_status")
async def system_status(
    registry=Depends(get_provider_registry),
    cloud_provider: str = Depends(get_cloud_provider),
):
    """Detailed system status with service connectivity."""
    status_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cloud_provider": cloud_provider,
        "services": {},
    }

    try:
        authenticator = registry.get_authenticator()
        status_info["services"]["cloud"] = {
            "provider": authenticator.get_provider_name(),
            "authenticated": authenticator.is_authenticated(),
        }
    except Exception as e:
        status_info["services"]["cloud"] = {"authenticated": False, "error": str(e)}

    return status_info
