"""Analysis, dashboard, and chart data endpoints."""

import json
import logging
import asyncio
import threading
from typing import Dict, Any, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from presentation.api.v2.schemas.clusters import AnalysisStatus
from presentation.api.v2.schemas.analysis import ChartDataResponse, CPUOptimizationPlan
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import (
    get_cluster_manager, get_cpu_report_exporter,
    get_analysis_results, get_analysis_cache,
)

logger = logging.getLogger(__name__)


def _sanitize_numpy(obj):
    """Recursively convert numpy types to native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_numpy(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/clusters/{cluster_id:path}/analyze")
async def analyze_cluster(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Trigger analysis for a cluster. Returns session key for progress tracking."""
    try:
        from infrastructure.services.background_processor import run_subscription_aware_background_analysis

        cluster_info = cluster_manager.get_cluster(cluster_id)
        if not cluster_info:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        resource_group = cluster_info.get('resource_group', '')
        cluster_name = cluster_info.get('name', '')
        subscription_id = cluster_info.get('subscription_id')
        cloud_provider = cluster_info.get('cloud_provider', 'azure')
        region = cluster_info.get('region', '')

        thread = threading.Thread(
            target=run_subscription_aware_background_analysis,
            args=(cluster_id, resource_group, cluster_name),
            kwargs={'subscription_id': subscription_id, 'cloud_provider': cloud_provider, 'region': region},
            daemon=True,
        )
        thread.start()

        return {
            "session_key": cluster_id,
            "status": "started",
            "message": f"Analysis started for {cluster_id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start analysis for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {e}")


@router.get("/clusters/{cluster_id:path}/analysis-status", response_model=AnalysisStatus)
async def analysis_status(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get current analysis status for a cluster."""
    try:
        status_data = cluster_manager.get_analysis_status(cluster_id)
        if not status_data:
            return AnalysisStatus(session_key=cluster_id, status="not_started")
        return AnalysisStatus(
            session_key=status_data.get('session_key', cluster_id),
            status=status_data.get('status', 'unknown'),
            progress=status_data.get('progress', 0.0),
            current_phase=status_data.get('current_phase'),
            message=status_data.get('message'),
            started_at=status_data.get('started_at'),
            completed_at=status_data.get('completed_at'),
            error=status_data.get('error'),
        )
    except Exception as e:
        logger.error(f"Failed to get analysis status for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis status")


@router.get("/clusters/{cluster_id:path}/analysis-progress-stream")
async def analysis_progress_stream(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """SSE stream for real-time analysis progress updates."""
    async def event_generator():
        try:
            from shared.config.config import analysis_status_tracker
            no_data_count = 0
            while True:
                # Read from in-memory tracker first (updated by background_processor)
                status_data = analysis_status_tracker.get(cluster_id)
                if not status_data:
                    # Fallback to DB
                    status_data = cluster_manager.get_analysis_status(cluster_id)
                if status_data:
                    no_data_count = 0
                    yield f"data: {json.dumps(status_data)}\n\n"
                    if status_data.get('status') in ('completed', 'failed', 'error'):
                        break
                else:
                    no_data_count += 1
                    if no_data_count > 30:  # 30 seconds with no data, stop
                        yield f"data: {json.dumps({'status': 'error', 'message': 'No analysis status found'})}\n\n"
                        break
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chart-data")
async def chart_data(
    cluster_id: Optional[str] = Query(None),
    chart_type: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get chart data for dashboard visualization.

    Most generators output Recharts format directly (array-of-objects).
    Savings and insights need minor normalization; HPA still needs conversion.
    """
    try:
        from presentation.api import chart_generator
        from shared.utils.shared import _get_analysis_data

        empty_result = {
            'cost_breakdown': [],
            'resource_utilization': [],
            'hpa_comparison': [],
            'savings_breakdown': {},
            'namespace_costs': [],
            'workload_costs': [],
            'insights': [],
            'trend_data': [],
        }

        analysis_data = None
        if cluster_id:
            analysis_data, data_source = _get_analysis_data(cluster_id)
            logger.info(f"Chart data using source: {data_source} for {cluster_id}")

        if not analysis_data:
            return empty_result

        def _safe(fn, *args):
            try:
                return fn(*args)
            except Exception as exc:
                logger.debug(f"Chart generator {fn.__name__} skipped: {exc}")
                return None

        # --- All generators output Recharts format directly ---

        # savings_breakdown: dict pass-through with float normalization
        raw_savings = _safe(chart_generator.extract_standards_based_savings, analysis_data)
        savings = {}
        if raw_savings and isinstance(raw_savings, dict):
            savings = {k: float(v) if isinstance(v, (int, float)) else v for k, v in raw_savings.items()}

        # insights: dict of category→message → normalize to [{category, message}]
        raw_insights = _safe(chart_generator.generate_insights, analysis_data)
        insight_items = []
        if raw_insights and isinstance(raw_insights, dict):
            for cat, val in raw_insights.items():
                if isinstance(val, str):
                    insight_items.append({'category': cat, 'message': val})
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str):
                            insight_items.append({'category': cat, 'message': item})
                        elif isinstance(item, dict):
                            insight_items.append({**item, 'category': cat})
        elif isinstance(raw_insights, list):
            insight_items = raw_insights

        return _sanitize_numpy({
            'cost_breakdown': _safe(chart_generator.generate_pod_cost_data, analysis_data) or [],
            'resource_utilization': _safe(chart_generator.generate_node_utilization_data, analysis_data) or [],
            'hpa_comparison': _safe(chart_generator.generate_dynamic_hpa_comparison, analysis_data) or [],
            'savings_breakdown': savings,
            'namespace_costs': _safe(chart_generator.generate_namespace_data, analysis_data) or [],
            'workload_costs': _safe(chart_generator.generate_workload_data, analysis_data) or [],
            'insights': insight_items,
            'trend_data': (_safe(chart_generator.generate_dynamic_trend_data, cluster_id, analysis_data) if cluster_id else None) or [],
        })
    except Exception as e:
        logger.error(f"Failed to get chart data: {e}", exc_info=True)
        return {
            'cost_breakdown': [], 'resource_utilization': [], 'hpa_comparison': [],
            'savings_breakdown': {}, 'namespace_costs': [], 'workload_costs': [],
            'insights': [], 'trend_data': [],
        }


@router.get("/dashboard/overview")
async def dashboard_overview(
    cluster_id: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get dashboard overview data for a cluster."""
    try:
        from shared.utils.shared import _get_analysis_data

        # Get cluster base info from DB
        cluster_info = cluster_manager.get_cluster(cluster_id) if cluster_id else None
        cluster_name = (cluster_info or {}).get('name', cluster_id or 'unknown')

        # Get analysis data
        analysis_data, data_source = _get_analysis_data(cluster_id) if cluster_id else (None, 'no_cluster_id')

        overview = {
            'cluster_name': cluster_name,
            'cloud_provider': (cluster_info or {}).get('cloud_provider', 'azure'),
            'optimization_score': 0.0,
            'total_monthly_cost': 0.0,
            'potential_savings': 0.0,
            'node_count': 0,
            'pod_count': 0,
            'health_score': 0.0,
            'top_recommendations': [],
        }

        if cluster_info:
            overview['total_monthly_cost'] = float(cluster_info.get('last_cost', 0) or 0)
            overview['potential_savings'] = float(cluster_info.get('last_savings', 0) or 0)
            overview['optimization_score'] = float(cluster_info.get('last_confidence', 0) or 0)

        if analysis_data:
            # Override with richer analysis data if available
            overview['total_monthly_cost'] = float(analysis_data.get('total_cost', overview['total_monthly_cost']) or 0)
            overview['potential_savings'] = float(analysis_data.get('total_savings', overview['potential_savings']) or 0)
            overview['optimization_score'] = float(analysis_data.get('confidence_score', overview['optimization_score']) or 0)
            overview['health_score'] = float(analysis_data.get('current_health_score', 0) or 0)
            overview['node_count'] = int(analysis_data.get('current_node_count', analysis_data.get('node_count', 0)) or 0)
            # Count pods from kubectl data if available
            pods_data = analysis_data.get('pods', analysis_data.get('pod_data', []))
            if isinstance(pods_data, list):
                overview['pod_count'] = len(pods_data)
            elif isinstance(pods_data, int):
                overview['pod_count'] = pods_data
            # Top recommendations
            recs = analysis_data.get('recommendations', analysis_data.get('top_recommendations', []))
            if isinstance(recs, list):
                overview['top_recommendations'] = recs[:5]

        return _sanitize_numpy(overview)
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}", exc_info=True)
        return {'cluster_name': cluster_id or 'unknown', 'optimization_score': 0, 'total_monthly_cost': 0, 'potential_savings': 0}


@router.get("/dashboard/recent-analysis")
async def recent_analysis(
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get most recent analysis results."""
    try:
        from shared.utils.shared import _get_analysis_data

        # Find the most recently analyzed cluster
        clusters = cluster_manager.get_all_clusters() or []
        # Sort by last_analyzed descending, filter to those with analysis data
        analyzed = [c for c in clusters if c.get('last_analyzed')]
        analyzed.sort(key=lambda c: c.get('last_analyzed', ''), reverse=True)

        for c in analyzed:
            cid = c.get('cluster_id', c.get('id', ''))
            if cid:
                data, source = _get_analysis_data(cid)
                if data:
                    return {
                        'cluster_id': cid,
                        'cluster_name': c.get('name', c.get('cluster_name', '')),
                        'last_analyzed': c.get('last_analyzed', ''),
                        'total_cost': float(data.get('total_cost', 0) or 0),
                        'total_savings': float(data.get('total_savings', 0) or 0),
                        'confidence_score': float(data.get('confidence_score', 0) or 0),
                        'health_score': float(data.get('current_health_score', 0) or 0),
                        'node_count': int(data.get('current_node_count', data.get('node_count', 0)) or 0),
                        'data_source': source,
                    }
        return {}
    except Exception as e:
        logger.error(f"Failed to get recent analysis: {e}", exc_info=True)
        return {}


@router.get("/clusters/{cluster_id:path}/cpu-optimization-plan")
async def cpu_optimization_plan(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Generate CPU optimization plan for a cluster."""
    try:
        plan = cluster_manager.get_cpu_optimization_plan(cluster_id)
        return plan or {"cluster_id": cluster_id, "plan": {}, "recommendations": []}
    except Exception as e:
        logger.error(f"Failed to generate CPU optimization plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plan")


@router.get("/clusters/{cluster_id:path}/cpu-optimization-script")
async def cpu_optimization_script(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    exporter=Depends(get_cpu_report_exporter),
):
    """Export CPU optimization as executable script."""
    try:
        if hasattr(exporter, 'export_script'):
            script = exporter.export_script(cluster_id)
            return StreamingResponse(
                iter([script]),
                media_type="text/x-sh",
                headers={"Content-Disposition": f"attachment; filename=cpu-optimization-{cluster_id}.sh"},
            )
    except Exception as e:
        logger.error(f"Failed to export CPU script: {e}")
    raise HTTPException(status_code=500, detail="Failed to export script")


@router.get("/clusters/{cluster_id:path}/cpu-report")
async def cpu_report(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    exporter=Depends(get_cpu_report_exporter),
):
    """Export CPU optimization report."""
    try:
        if hasattr(exporter, 'export_report'):
            return exporter.export_report(cluster_id)
    except Exception as e:
        logger.error(f"Failed to export CPU report: {e}")
    raise HTTPException(status_code=500, detail="Failed to export report")


@router.get("/debug-analysis")
async def debug_analysis(
    user: Dict[str, Any] = Depends(get_current_user),
    results: Dict[str, Any] = Depends(get_analysis_results),
    cache: Dict[str, Any] = Depends(get_analysis_cache),
):
    """Debug endpoint showing raw analysis data."""
    try:
        return {
            "cached_clusters": list(cache.get('clusters', {}).keys()),
            "active_results": len(results),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/cache/clear")
@router.post("/cache/clear")
async def clear_cache(
    user: Dict[str, Any] = Depends(get_current_user),
    cache: Dict[str, Any] = Depends(get_analysis_cache),
):
    """Clear analysis cache."""
    try:
        cache['clusters'] = {}
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")
