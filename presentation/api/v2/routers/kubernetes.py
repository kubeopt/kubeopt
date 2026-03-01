"""Kubernetes data API endpoints."""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from presentation.api.v2.schemas.kubernetes import PodsOverview, WorkloadsOverview, ResourcesOverview
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_kubernetes_dashboard, get_cluster_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kubernetes", tags=["kubernetes"])


def _resolve_subscription(cluster_id: str, subscription_id: Optional[str], cluster_manager) -> str:
    """Resolve subscription_id — look it up from DB if not provided."""
    if subscription_id:
        return subscription_id
    try:
        info = cluster_manager.get_cluster(cluster_id)
        if info:
            return info.get('subscription_id', '') or 'default'
    except Exception:
        pass
    return 'default'


@router.get("/pods/{cluster_id:path}/{subscription_id}")
async def get_pods_overview(
    cluster_id: str,
    subscription_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
):
    """Get pods overview for a cluster."""
    try:
        data = dashboard.get_pods_overview(cluster_id, subscription_id or 'default')
        return data or {"cluster_id": cluster_id, "pods": [], "total_pods": 0}
    except Exception as e:
        logger.error(f"Failed to get pods for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pods overview")


@router.get("/pods-by-cluster")
async def get_pods_by_cluster(
    cluster_id: str = Query(...),
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get pods overview for a cluster (subscription auto-resolved)."""
    try:
        sub_id = _resolve_subscription(cluster_id, None, cluster_manager)
        data = dashboard.get_pods_overview(cluster_id, sub_id)
        return data or {"cluster_id": cluster_id, "pods": [], "total_pods": 0}
    except Exception as e:
        logger.error(f"Failed to get pods for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pods overview")


@router.get("/workloads/{cluster_id:path}/{subscription_id}")
async def get_workloads_overview(
    cluster_id: str,
    subscription_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
):
    """Get workloads overview for a cluster."""
    try:
        data = dashboard.get_workloads_overview(cluster_id, subscription_id or 'default')
        return data or {"cluster_id": cluster_id, "deployments": [], "total_workloads": 0}
    except Exception as e:
        logger.error(f"Failed to get workloads for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workloads overview")


@router.get("/workloads-by-cluster")
async def get_workloads_by_cluster(
    cluster_id: str = Query(...),
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get workloads overview (subscription auto-resolved)."""
    try:
        sub_id = _resolve_subscription(cluster_id, None, cluster_manager)
        data = dashboard.get_workloads_overview(cluster_id, sub_id)
        return data or {"cluster_id": cluster_id, "deployments": [], "total_workloads": 0}
    except Exception as e:
        logger.error(f"Failed to get workloads for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workloads overview")


@router.get("/resources/{cluster_id:path}/{subscription_id}")
async def get_resources_overview(
    cluster_id: str,
    subscription_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
):
    """Get resources overview for a cluster."""
    try:
        data = dashboard.get_resources_overview(cluster_id, subscription_id or 'default')
        return data or {"cluster_id": cluster_id, "nodes": []}
    except Exception as e:
        logger.error(f"Failed to get resources for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get resources overview")


@router.get("/resources-by-cluster")
async def get_resources_by_cluster(
    cluster_id: str = Query(...),
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get resources overview (subscription auto-resolved)."""
    try:
        sub_id = _resolve_subscription(cluster_id, None, cluster_manager)
        data = dashboard.get_resources_overview(cluster_id, sub_id)
        return data or {"cluster_id": cluster_id, "nodes": []}
    except Exception as e:
        logger.error(f"Failed to get resources for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get resources overview")


@router.get("/dashboard/{cluster_id:path}/{subscription_id}")
async def get_unified_dashboard(
    cluster_id: str,
    subscription_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    dashboard=Depends(get_kubernetes_dashboard),
):
    """Get unified dashboard data combining pods, workloads, and resources."""
    try:
        data = dashboard.get_unified_dashboard(cluster_id, subscription_id)
        return data or {"cluster_id": cluster_id}
    except Exception as e:
        logger.error(f"Failed to get unified dashboard for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")
