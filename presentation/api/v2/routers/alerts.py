"""Alerts CRUD endpoints."""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_alerts_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["alerts"])


class AlertCreateRequest(BaseModel):
    name: str
    alert_type: str = "cost_threshold"
    threshold: Optional[float] = None
    cluster_id: Optional[str] = None
    enabled: bool = True


class AlertUpdateRequest(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None


@router.get("/alerts")
async def get_alerts(
    cluster_id: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Get all alerts, optionally filtered by cluster."""
    try:
        return alerts_mgr.get_alerts_route(cluster_id)
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.post("/alerts")
async def create_alert(
    body: AlertCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Create a new alert."""
    try:
        return alerts_mgr.create_alert_route(body.model_dump())
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.put("/alerts/{alert_id}")
async def update_alert(
    alert_id: int,
    body: AlertUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Update an existing alert."""
    try:
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        return alerts_mgr.update_alert_route(alert_id, updates)
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert")


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Delete an alert."""
    try:
        return alerts_mgr.delete_alert_route(alert_id)
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert")
