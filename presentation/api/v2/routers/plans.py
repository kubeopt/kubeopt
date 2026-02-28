"""Implementation plan endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from presentation.api.v2.schemas.plans import PlanGenerateRequest, PlanResponse
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.license import check_license
from presentation.api.v2.dependencies.services import get_cluster_manager, get_external_api_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["plans"])


@router.get("/clusters/{cluster_id:path}/plan")
async def get_cluster_plan(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get the latest implementation plan for a cluster."""
    try:
        plan = cluster_manager.get_latest_plan(cluster_id)
        if plan:
            return plan
        return {"cluster_id": cluster_id, "plan": None, "message": "No plan available"}
    except Exception as e:
        logger.error(f"Failed to get plan for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get plan")


@router.get("/clusters/{cluster_id:path}/plans")
async def get_plan_history(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get plan history for a cluster."""
    try:
        if hasattr(cluster_manager, 'get_plan_history'):
            history = cluster_manager.get_plan_history(cluster_id)
            return {"plans": history or [], "total": len(history or [])}
        return {"plans": [], "total": 0}
    except Exception as e:
        logger.error(f"Failed to get plan history for {cluster_id}: {e}")
        return {"plans": [], "total": 0}


@router.get("/plans/{plan_id:path}")
async def get_plan_by_id(
    plan_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get a specific plan by ID."""
    try:
        if hasattr(cluster_manager, 'get_plan_by_id'):
            plan = cluster_manager.get_plan_by_id(plan_id)
            if plan:
                return plan
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get plan")


@router.post("/clusters/{cluster_id:path}/plan/generate")
async def generate_plan(
    cluster_id: str,
    body: PlanGenerateRequest = PlanGenerateRequest(),
    user: Dict[str, Any] = Depends(get_current_user),
    license_info: Dict[str, Any] = Depends(check_license),
    api_client=Depends(get_external_api_client),
):
    """Generate an AI implementation plan for a cluster (requires license)."""
    try:
        if hasattr(api_client, 'generate_plan'):
            result = api_client.generate_plan(
                cluster_id=cluster_id,
                strategy=body.strategy,
                force=body.force_regenerate,
            )
            return result or {"status": "error", "message": "Plan generation returned no result"}
    except Exception as e:
        logger.error(f"Failed to generate plan for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {e}")


@router.get("/implementation-plan")
async def get_implementation_plan(
    cluster_id: str = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get implementation plan (legacy endpoint)."""
    try:
        plan = cluster_manager.get_latest_plan(cluster_id)
        return plan or {}
    except Exception as e:
        logger.error(f"Failed to get implementation plan: {e}")
        return {}


@router.get("/plan-costs/summary")
async def plan_costs_summary(
    cluster_id: str = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get plan costs summary."""
    try:
        costs = cluster_manager.get_plan_costs_summary(cluster_id)
        return costs or {}
    except Exception as e:
        logger.error(f"Failed to get plan costs: {e}")
        return {}
