"""Scheduler management endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
async def scheduler_status(
    user: Dict[str, Any] = Depends(get_current_user),
    scheduler=Depends(get_scheduler),
):
    """Get auto-analysis scheduler status."""
    try:
        if hasattr(scheduler, 'get_status'):
            return scheduler.get_status()
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
    return {"running": False, "message": "Scheduler not available"}


@router.post("/start")
async def start_scheduler(
    user: Dict[str, Any] = Depends(get_current_user),
    scheduler=Depends(get_scheduler),
):
    """Start the auto-analysis scheduler."""
    try:
        if hasattr(scheduler, 'start'):
            scheduler.start()
            return {"message": "Scheduler started", "running": True}
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    raise HTTPException(status_code=500, detail="Failed to start scheduler")


@router.post("/stop")
async def stop_scheduler(
    user: Dict[str, Any] = Depends(get_current_user),
    scheduler=Depends(get_scheduler),
):
    """Stop the auto-analysis scheduler."""
    try:
        if hasattr(scheduler, 'stop'):
            scheduler.stop()
            return {"message": "Scheduler stopped", "running": False}
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
    raise HTTPException(status_code=500, detail="Failed to stop scheduler")


@router.post("/force-analysis")
async def force_analysis(
    user: Dict[str, Any] = Depends(get_current_user),
    scheduler=Depends(get_scheduler),
):
    """Force immediate analysis of all clusters."""
    try:
        if hasattr(scheduler, 'force_analysis'):
            scheduler.force_analysis()
            return {"message": "Analysis triggered for all clusters"}
    except Exception as e:
        logger.error(f"Failed to force analysis: {e}")
    raise HTTPException(status_code=500, detail="Failed to trigger analysis")
