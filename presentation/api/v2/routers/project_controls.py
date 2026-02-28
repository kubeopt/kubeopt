"""Project controls and environment configuration endpoints."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from presentation.api.v2.schemas.project_controls import EnvironmentsUpdateRequest
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_cluster_manager, get_analysis_results

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["project-controls"])

_CONFIG_DIR = Path(__file__).resolve().parents[4] / "config"


@router.get("/environments")
async def get_environments():
    """Get customer-configurable environments."""
    config_path = _CONFIG_DIR / "environments.json"
    if not config_path.exists():
        return {
            "status": "success",
            "environments": {},
            "default_environment": "development",
            "total_environments": 0,
        }

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        return {
            "status": "success",
            "environments": config.get("environments", {}),
            "default_environment": config.get("default_environment", "development"),
            "total_environments": len(config.get("environments", {})),
        }
    except Exception as e:
        logger.error(f"Failed to get environments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/environments")
async def update_environments(
    body: EnvironmentsUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Update customer environment configuration."""
    try:
        config = {
            "environments": {k: v.model_dump() for k, v in body.environments.items()},
            "default_environment": body.default_environment,
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "description": "Customer-configured environments",
            },
        }

        config_path = _CONFIG_DIR / "environments.json"
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Updated environment configuration with {len(body.environments)} environments")

        return {
            "status": "success",
            "message": f"Updated {len(body.environments)} environments",
            "environments_count": len(body.environments),
        }
    except Exception as e:
        logger.error(f"Failed to update environments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-controls")
async def project_controls(
    cluster_id: str = Query(None),
    request: Request = None,
    cluster_mgr=Depends(get_cluster_manager),
    analysis_results: Dict[str, Any] = Depends(get_analysis_results),
):
    """Get project controls framework data."""
    from presentation.api.project_controls_api import sanitize_for_json
    from shared.utils.shared import _get_analysis_data

    # Resolve cluster_id from query or referer
    if not cluster_id and request:
        referrer = request.headers.get("referer", "")
        if "/cluster/" in referrer:
            try:
                cluster_id = referrer.split("/cluster/")[-1].split("/")[0].split("?")[0]
            except Exception:
                pass

    if not cluster_id:
        raise HTTPException(status_code=400, detail="No cluster ID provided for project controls")

    cluster = cluster_mgr.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    current_analysis, data_source = _get_analysis_data(cluster_id)
    if not current_analysis:
        raise HTTPException(
            status_code=404,
            detail="No analysis data available for project controls. Please run analysis first.",
        )

    framework_data = {
        "status": "migrated",
        "message": "Project Controls has been upgraded to Enterprise Operational Metrics.",
        "framework": {},
        "execution_plan": {},
        "metadata": {
            "cluster_id": cluster_id,
            "cluster_name": cluster["name"],
            "resource_group": cluster["resource_group"],
            "subscription_id": cluster.get("subscription_id"),
            "subscription_name": cluster.get("subscription_name"),
            "data_source": data_source,
            "generated_at": datetime.now().isoformat(),
            "framework_version": "2.0.0-fixed",
            "analysis_timestamp": current_analysis.get("analyzed_at"),
            "real_data_only": True,
            "commands_extracted": True,
        },
    }

    return sanitize_for_json(framework_data)
