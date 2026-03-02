"""Implementation plan endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from presentation.api.v2.schemas.plans import PlanGenerateRequest, PlanResponse
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.license import check_license
from presentation.api.v2.dependencies.services import get_cluster_manager, get_external_api_client
from infrastructure.services.license_validator import get_license_validator, Feature

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
    cluster_manager=Depends(get_cluster_manager),
):
    """Generate an AI implementation plan for a cluster (requires license)."""
    try:
        # Rate limit: check feature access and daily usage limit
        validator = get_license_validator()
        if not validator.has_feature(Feature.AI_PLAN_GENERATION):
            raise HTTPException(
                status_code=403,
                detail="AI plan generation requires a PRO or ENTERPRISE license"
            )

        allowed, limit_msg = validator.check_usage_limit('plans_per_day')
        if not allowed:
            status = validator.get_plan_generation_status()
            raise HTTPException(
                status_code=429,
                detail={
                    "message": limit_msg,
                    "daily_limit": status.get("daily_limit"),
                    "next_reset": status.get("next_reset"),
                    "hours_until_reset": status.get("hours_until_reset"),
                }
            )

        from shared.utils.shared import _get_analysis_data

        # Get cluster name from DB
        cluster_info = cluster_manager.get_cluster(cluster_id)
        cluster_name = (cluster_info or {}).get('name', cluster_id)

        # Get latest analysis data — required for plan generation
        analysis_data, _ = _get_analysis_data(cluster_id)
        if not analysis_data:
            raise HTTPException(status_code=400, detail="No analysis data available. Run an analysis first.")

        # Use compact enhanced_analysis_input if available (stored during analysis).
        # The full raw analysis_data can be massive and cause timeouts on the remote API.
        plan_input = analysis_data.get('enhanced_analysis_input') or analysis_data
        if plan_input is not analysis_data:
            logger.info(f"Using compact enhanced_analysis_input for plan generation ({cluster_id})")
        else:
            # Fallback: try loading from DB enhanced_analysis_data column
            try:
                import sqlite3, json as _json
                db_path = cluster_manager.db_path
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        'SELECT enhanced_analysis_data FROM clusters WHERE id = ?', (cluster_id,)
                    ).fetchone()
                    if row and row['enhanced_analysis_data']:
                        raw = row['enhanced_analysis_data']
                        eai = _json.loads(raw.decode('utf-8') if isinstance(raw, bytes) else raw)
                        if isinstance(eai, dict) and eai:
                            plan_input = eai
                            logger.info(f"Using enhanced_analysis_data from DB for plan generation ({cluster_id})")
            except Exception as eai_err:
                logger.debug(f"Enhanced analysis data DB fallback failed: {eai_err}")

        if hasattr(api_client, 'generate_plan'):
            success, result = api_client.generate_plan(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                analysis_data=plan_input,
            )
            if success:
                # Store the plan in DB so GET /plan returns it
                try:
                    cluster_manager.store_implementation_plan(cluster_id, result)
                    logger.info(f"Stored generated plan for {cluster_id}")
                except Exception as store_err:
                    logger.warning(f"Failed to store plan (returning anyway): {store_err}")
                return result
            return {"status": "error", "message": result.get('error', 'Plan generation failed'), **result}
        raise HTTPException(status_code=500, detail="Plan generation service not configured")
    except HTTPException:
        raise
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


@router.get("/plan-generation/status")
async def plan_generation_status(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Get plan generation availability and remaining daily quota."""
    validator = get_license_validator()
    return validator.get_plan_generation_status()
