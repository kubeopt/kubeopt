"""Alerts CRUD endpoints."""

import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_alerts_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["alerts"])

# Fields stored in the metadata JSON column (not direct DB columns)
_METADATA_FIELDS = {'severity', 'metric_name', 'operator', 'frequency', 'notification_email'}


def _normalize_alert_for_frontend(alert: Dict) -> Dict:
    """Normalize a raw DB alert dict to the schema the frontend expects."""
    if not alert:
        return alert
    # Extract extra fields from metadata
    meta = alert.get('metadata', {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    out = {
        'id': alert.get('id'),
        'name': alert.get('name', ''),
        'alert_type': alert.get('alert_type', 'cost_threshold'),
        'threshold': alert.get('threshold_amount'),
        'cluster_id': alert.get('cluster_id'),
        'enabled': alert.get('status') != 'paused',
        'status': alert.get('status', 'active'),
        'severity': meta.get('severity', 'warning'),
        'description': alert.get('description', ''),
        'metric_name': meta.get('metric_name', 'cost'),
        'operator': meta.get('operator', '>'),
        'frequency': meta.get('frequency', alert.get('notification_frequency', 'hourly')),
        'notification_email': meta.get('notification_email', ''),
        'created_at': alert.get('created_at', ''),
        'updated_at': alert.get('updated_at', ''),
    }
    return out


def _prepare_alert_data(data: Dict) -> Dict:
    """Prepare frontend data for the alerts manager / DB layer."""
    result = dict(data)
    # Map threshold -> threshold_amount
    if 'threshold' in result:
        result['threshold_amount'] = result.pop('threshold') or 0
    result.setdefault('threshold_amount', 0)
    # Provide defaults the DB requires
    result.setdefault('cluster_name', result.get('cluster_id', ''))
    result.setdefault('resource_group', '')
    # Pack extra fields into metadata
    meta = {}
    for key in list(result.keys()):
        if key in _METADATA_FIELDS:
            meta[key] = result.pop(key)
    if meta:
        result['metadata'] = json.dumps(meta)
    # Map frequency to notification_frequency
    if 'frequency' in meta:
        freq_map = {'realtime': 'immediate', 'hourly': 'hourly', 'daily': 'daily', 'weekly': 'weekly'}
        result['notification_frequency'] = freq_map.get(meta['frequency'], 'daily')
    return result


class AlertCreateRequest(BaseModel):
    name: str
    alert_type: str = "cost_threshold"
    threshold: Optional[float] = None
    cluster_id: Optional[str] = None
    enabled: bool = True
    severity: Optional[str] = "warning"
    description: Optional[str] = None
    metric_name: Optional[str] = None
    operator: Optional[str] = ">"
    frequency: Optional[str] = "hourly"
    notification_email: Optional[str] = None


class AlertUpdateRequest(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    metric_name: Optional[str] = None
    operator: Optional[str] = None
    frequency: Optional[str] = None
    notification_email: Optional[str] = None


@router.get("/alerts")
async def get_alerts(
    cluster_id: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Get all alerts, optionally filtered by cluster."""
    try:
        result = alerts_mgr.get_alerts_route(cluster_id)
        raw_alerts = result.get('alerts', [])
        alerts_list = [_normalize_alert_for_frontend(a) for a in raw_alerts]
        return {
            'alerts': alerts_list,
            'total': len(alerts_list),
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return {'alerts': [], 'total': 0}


@router.post("/alerts")
async def create_alert(
    body: AlertCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Create a new alert."""
    try:
        alert_data = _prepare_alert_data(body.model_dump(exclude_none=True))
        result = alerts_mgr.create_alert_route(alert_data)
        if result.get('status') == 'error':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to create alert'))
        # Normalize the returned alert
        if 'alert' in result and result['alert']:
            result['alert'] = _normalize_alert_for_frontend(result['alert'])
        return result
    except HTTPException:
        raise
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
        raw = {k: v for k, v in body.model_dump().items() if v is not None}
        # Handle enabled -> status mapping
        if 'enabled' in raw:
            raw['status'] = 'active' if raw.pop('enabled') else 'paused'
        updates = _prepare_alert_data(raw)
        result = alerts_mgr.update_alert_route(alert_id, updates)
        if result.get('status') == 'error':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to update alert'))
        if 'alert' in result and result['alert']:
            result['alert'] = _normalize_alert_for_frontend(result['alert'])
        return result
    except HTTPException:
        raise
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
        result = alerts_mgr.delete_alert_route(alert_id)
        if result.get('status') == 'error':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to delete alert'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert")
