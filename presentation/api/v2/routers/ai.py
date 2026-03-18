"""
AI Chat router — proxies requests to the hosted AI chat service.

Gathers cluster context locally and sends to ai.kubeopt.com for processing.
"""

import json
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from presentation.api.v2.dependencies.auth import get_current_user, create_service_jwt_token
from presentation.api.v2.dependencies.services import get_cluster_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

# AI service URL — hosted on Railway, like plan-generation
import os
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "https://ai.kubeopt.com")


class ChatRequest(BaseModel):
    message: str
    cluster_id: Optional[str] = None
    session_id: Optional[str] = None
    comparison_cluster_id: Optional[str] = None
    github_token: Optional[str] = None


class ConfirmProxyRequest(BaseModel):
    session_id: str
    tool_use_id: str
    approved: bool
    github_token: Optional[str] = None


def _gather_context(cluster_id: str, cluster_manager) -> Dict[str, Any]:
    """Gather cluster context to send to the AI service."""
    context = {"cluster": {}, "costs": {}, "utilization": {}, "recommendations": {}, "pod_costs": [], "node_data": [], "anomalies": [], "pricing": {}}
    analysis_data = None

    # Get cluster info
    cluster_info = cluster_manager.get_cluster(cluster_id)
    if cluster_info:
        context["cluster"] = {
            "name": cluster_info.get("cluster_name", ""),
            "region": cluster_info.get("region", ""),
            "cloud_provider": cluster_info.get("cloud_provider", "azure"),
            "node_count": cluster_info.get("node_count", 0),
            "pod_count": cluster_info.get("pod_count", 0),
        }

    # Get analysis data
    try:
        from shared.utils.shared import _get_analysis_data
        analysis_data, source = _get_analysis_data(cluster_id)  # noqa: F841 (source unused)
        if analysis_data:
            context["costs"] = {
                "total_monthly": round(analysis_data.get("total_cost", 0), 2),
                "total_savings": round(analysis_data.get("total_savings", 0), 2),
                "optimization_score": analysis_data.get("confidence_score", 0),
                "savings_breakdown": {},
            }

            # Savings breakdown
            try:
                from presentation.api import chart_generator
                savings = chart_generator.extract_standards_based_savings(analysis_data)
                if savings:
                    context["costs"]["savings_breakdown"] = {k: round(float(v), 2) if isinstance(v, (int, float)) else v for k, v in savings.items()}
            except Exception:
                pass

            context["utilization"] = {
                "avg_cpu": round(analysis_data.get("avg_cpu", 0), 1),
                "avg_memory": round(analysis_data.get("avg_memory", 0), 1),
            }

            # Recommendations from enhanced_analysis_input
            eai = analysis_data.get("enhanced_analysis_input", {})
            context["recommendations"] = {
                "node": eai.get("node_recommendations", eai.get("node_analysis", {}).get("recommendations", []))[:20],
                "hpa": eai.get("hpa_recommendations", [])[:20],
                "storage": eai.get("storage_recommendations", [])[:20],
                "cost": eai.get("cost_analysis", {}).get("recommendations", [])[:20],
            }

            # Pod costs
            try:
                from presentation.api import chart_generator
                pods = chart_generator.generate_workload_data(analysis_data)
                if pods:
                    context["pod_costs"] = sorted(pods, key=lambda p: p.get("cost", p.get("monthly_cost", 0)), reverse=True)[:30]
            except Exception:
                pass

            # Node data
            context["node_data"] = analysis_data.get("nodes", [])[:20]

            # Anomalies
            context["anomalies"] = analysis_data.get("anomalies", [])[:10]

            # Pricing data from analysis
            context["pricing"] = {
                "vm_prices": eai.get("vm_pricing", {}),
            }
    except Exception as e:
        logger.warning(f"Failed to gather analysis context: {e}")

    # Analysis metadata for AI freshness/confidence awareness
    analysis_metadata = {
        "cloud_provider": cluster_info.get("cloud_provider", "azure") if cluster_info else "unknown",
        "node_count_analyzed": context["cluster"].get("node_count", 0),
        "pod_count_analyzed": context["cluster"].get("pod_count", 0),
    }

    # Data freshness — try in-memory tracker first, fall back to DB
    try:
        from shared.config.config import analysis_status_tracker
        import time as _time
        from datetime import datetime, timezone
        tracker = analysis_status_tracker.get(cluster_id, {})
        completed_at = tracker.get("completed_at") or tracker.get("start_time")
        if completed_at:
            analysis_metadata["last_analyzed_at"] = datetime.fromtimestamp(completed_at, tz=timezone.utc).isoformat()
            analysis_metadata["data_age_minutes"] = round((_time.time() - completed_at) / 60)
    except Exception:
        pass

    # Fall back to DB cache timestamp if tracker didn't have it
    if "last_analyzed_at" not in analysis_metadata:
        try:
            last_analyzed = cluster_info.get("last_analyzed") if cluster_info else None
            if last_analyzed:
                import time as _time
                from datetime import datetime, timezone
                if isinstance(last_analyzed, (int, float)):
                    analysis_metadata["last_analyzed_at"] = datetime.fromtimestamp(last_analyzed, tz=timezone.utc).isoformat()
                    analysis_metadata["data_age_minutes"] = round((_time.time() - last_analyzed) / 60)
                elif isinstance(last_analyzed, str):
                    analysis_metadata["last_analyzed_at"] = last_analyzed
                    try:
                        parsed = datetime.fromisoformat(last_analyzed)
                        analysis_metadata["data_age_minutes"] = round((_time.time() - parsed.timestamp()) / 60)
                    except (ValueError, OSError):
                        pass
        except Exception:
            pass

    # Confidence score
    if analysis_data:
        analysis_metadata["overall_confidence"] = analysis_data.get("confidence_score")

    context["analysis_metadata"] = analysis_metadata

    return context


def _auto_detect_cluster(cluster_manager) -> Optional[str]:
    try:
        clusters = cluster_manager.get_all_clusters()
        if clusters and len(clusters) == 1:
            return clusters[0].get("cluster_id", clusters[0].get("id"))
    except Exception:
        pass
    return None


@router.post("/chat")
async def ai_chat(
    req: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Proxy AI chat to the hosted AI service."""
    # Resolve cluster
    cluster_id = req.cluster_id
    if not cluster_id:
        cluster_id = _auto_detect_cluster(cluster_manager)
    if not cluster_id:
        raise HTTPException(status_code=400, detail="cluster_id required")

    cluster_info = cluster_manager.get_cluster(cluster_id)
    if not cluster_info:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    # Gather context
    context = _gather_context(cluster_id, cluster_manager)

    # Comparison context for multi-cluster compare
    if req.comparison_cluster_id:
        comp_info = cluster_manager.get_cluster(req.comparison_cluster_id)
        if comp_info:
            context["comparison_context"] = _gather_context(req.comparison_cluster_id, cluster_manager)

    cloud_provider = cluster_info.get("cloud_provider", "azure")

    # Get license key for auth
    from infrastructure.services.license_validator import get_license_validator
    validator = get_license_validator()
    license_key = validator.license_key if hasattr(validator, 'license_key') else os.getenv("LICENSE_KEY", "")

    # Create service JWT for inter-service auth
    jwt_token = create_service_jwt_token(license_key)

    # Build request for AI service
    payload = {
        "message": req.message,
        "cluster_id": cluster_id,
        "session_id": req.session_id,
        "license_key": license_key,
        "cloud_provider": cloud_provider,
        "context": context,
        "github_token": req.github_token,
    }

    async def proxy_stream():
        """Stream SSE from AI service to client."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
                async with client.stream(
                    "POST",
                    f"{AI_SERVICE_URL}/v1/chat",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        try:
                            detail = json.loads(body).get("detail", body.decode())
                        except Exception:
                            detail = body.decode()
                        yield f"data: {json.dumps({'type': 'error', 'message': f'AI service error ({response.status_code}): {detail}'})}\n\n"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            yield f"{line}\n\n"

        except httpx.ConnectError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'AI service unavailable. Try again later.'})}\n\n"
        except Exception as e:
            logger.error(f"AI proxy error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'Proxy error: {str(e)}'})}\n\n"

    return StreamingResponse(
        proxy_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/chat/confirm")
async def ai_chat_confirm(
    req: ConfirmProxyRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Proxy confirmation to the AI service. Token passed opaquely."""
    from infrastructure.services.license_validator import get_license_validator
    validator = get_license_validator()
    license_key = validator.license_key if hasattr(validator, 'license_key') else os.getenv("LICENSE_KEY", "")
    jwt_token = create_service_jwt_token(license_key)

    payload = {
        "session_id": req.session_id,
        "tool_use_id": req.tool_use_id,
        "approved": req.approved,
        "github_token": req.github_token,
    }

    async def proxy_stream():
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
                async with client.stream(
                    "POST",
                    f"{AI_SERVICE_URL}/v1/chat/confirm",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        try:
                            detail = json.loads(body).get("detail", body.decode())
                        except Exception:
                            detail = body.decode()
                        yield f"data: {json.dumps({'type': 'error', 'message': f'AI service error ({response.status_code}): {detail}'})}\n\n"
                        return
                    async for line_data in response.aiter_lines():
                        if line_data.startswith("data: "):
                            yield f"{line_data}\n\n"
        except httpx.ConnectError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'AI service unavailable.'})}\n\n"
        except Exception as e:
            logger.error(f"AI confirm proxy error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'Proxy error: {str(e)}'})}\n\n"

    return StreamingResponse(
        proxy_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
