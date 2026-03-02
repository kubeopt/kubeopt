"""Analysis, dashboard, and chart data endpoints."""

import json
import logging
import asyncio
import re
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
        # Check in-memory tracker first (real-time updates from background_processor)
        from shared.config.config import analysis_status_tracker
        status_data = analysis_status_tracker.get(cluster_id)
        if not status_data:
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
            'cost_categories': [],
            'resource_utilization': [],
            'hpa_comparison': [],
            'savings_breakdown': {},
            'namespace_costs': [],
            'workload_costs': [],
            'insights': [],
            'trend_data': [],
            'node_recommendations': [],
            'anomaly_detection': {},
            'total_cost': 0,
            'cpu_gap': 0,
            'memory_gap': 0,
            'hpa_efficiency': 0,
            'namespace_count': 0,
            'workload_count': 0,
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
        _strip_html = re.compile(r'<[^>]+>').sub
        _strip_emoji = re.compile(
            r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F'
            r'\U0000200D\U00002702-\U000027B0\U0001FA00-\U0001FA6F'
            r'\U0001FA70-\U0001FAFF\U00002B50\U000023CF-\U000023FA]+',
        ).sub
        def _clean(text: str) -> str:
            return _strip_emoji('', _strip_html('', text)).strip()

        # Determine cloud provider for cloud-specific insight terminology
        _cloud_provider = analysis_data.get('cloud_provider', 'azure')
        if not _cloud_provider or _cloud_provider == 'azure':
            # Fall back to cluster DB info
            _cluster_info = cluster_manager.get_cluster(cluster_id) if cluster_id else None
            if _cluster_info:
                _cloud_provider = _cluster_info.get('cloud_provider', 'azure')

        raw_insights = _safe(chart_generator.generate_insights, analysis_data, _cloud_provider)
        insight_items = []
        if raw_insights and isinstance(raw_insights, dict):
            for cat, val in raw_insights.items():
                if isinstance(val, str):
                    insight_items.append({'category': cat, 'message': _clean(val)})
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str):
                            insight_items.append({'category': cat, 'message': _clean(item)})
                        elif isinstance(item, dict):
                            cleaned = {**item, 'category': cat}
                            if 'message' in cleaned:
                                cleaned['message'] = _clean(cleaned['message'])
                            insight_items.append(cleaned)
        elif isinstance(raw_insights, list):
            insight_items = [{**i, 'message': _clean(i.get('message', ''))} if isinstance(i, dict) and 'message' in i else i for i in raw_insights]

        # Extract node recommendations from enhanced_analysis_input
        node_recs = []
        try:
            eai = analysis_data.get('enhanced_analysis_input', {})
            # Fallback: if not in analysis_data, load from clusters table enhanced_analysis_data column
            if not eai and cluster_id:
                try:
                    import sqlite3, json
                    cluster_info_obj = cluster_manager.get_cluster(cluster_id)
                    if cluster_info_obj:
                        db_path = cluster_manager.db_path
                        with sqlite3.connect(db_path) as conn:
                            conn.row_factory = sqlite3.Row
                            row = conn.execute(
                                'SELECT enhanced_analysis_data FROM clusters WHERE id = ?', (cluster_id,)
                            ).fetchone()
                            if row and row['enhanced_analysis_data']:
                                raw = row['enhanced_analysis_data']
                                eai = json.loads(raw.decode('utf-8') if isinstance(raw, bytes) else raw)
                except Exception as e:
                    logger.debug(f"Enhanced data fallback failed: {e}")
            node_opt = eai.get('node_optimization', {}) if isinstance(eai, dict) else {}
            raw_recs = node_opt.get('recommendations', []) if isinstance(node_opt, dict) else []
            if isinstance(raw_recs, list):
                # Normalize field names: backend uses current_vm_size/recommended_vm_size,
                # frontend expects current_vm/recommended_vm
                for rec in raw_recs:
                    if isinstance(rec, dict):
                        if 'current_vm_size' in rec and 'current_vm' not in rec:
                            rec['current_vm'] = rec['current_vm_size']
                        if 'recommended_vm_size' in rec and 'recommended_vm' not in rec:
                            rec['recommended_vm'] = rec['recommended_vm_size']
                node_recs = raw_recs
        except Exception:
            pass

        # Extract anomaly detection data
        anomaly_data = {}
        try:
            raw_anomaly = analysis_data.get('anomaly_detection', {})
            if isinstance(raw_anomaly, dict) and raw_anomaly.get('total_anomalies', 0) > 0:
                anomaly_data = {
                    'total_anomalies': raw_anomaly.get('total_anomalies', 0),
                    'average_severity': raw_anomaly.get('average_severity', 0),
                    'highest_severity': raw_anomaly.get('highest_severity', 0),
                    'categories': raw_anomaly.get('anomaly_categories', {}),
                    'anomalies': (raw_anomaly.get('anomalies', []) or [])[:10],
                }
        except Exception:
            pass

        namespace_costs_result = _safe(chart_generator.generate_namespace_data, analysis_data) or []
        workload_costs_result = _safe(chart_generator.generate_workload_data, analysis_data) or []

        # Build category-based cost breakdown from analysis_data cost components
        cost_categories = []
        try:
            cat_map = [
                ('Compute (Nodes)', 'node_cost'),
                ('Storage', 'storage_cost'),
                ('Networking', 'networking_cost'),
                ('Control Plane', 'control_plane_cost'),
                ('Container Registry', 'registry_cost'),
                ('Monitoring', 'monitoring_cost'),
                ('Security', 'security_cost'),
            ]
            for label, key in cat_map:
                val = float(analysis_data.get(key, 0) or 0)
                if val > 0:
                    cost_categories.append({'name': label, 'value': round(val, 2)})
            # Roll up remaining minor categories into "Other"
            other_keys = ['keyvault_cost', 'application_services_cost', 'data_services_cost',
                          'integration_services_cost', 'devops_cost', 'backup_recovery_cost',
                          'governance_cost', 'support_management_cost', 'other_cost', 'system_cost']
            other_val = sum(float(analysis_data.get(k, 0) or 0) for k in other_keys)
            if other_val > 0:
                cost_categories.append({'name': 'Other Services', 'value': round(other_val, 2)})
        except Exception:
            pass

        return _sanitize_numpy({
            'cost_breakdown': _safe(chart_generator.generate_pod_cost_data, analysis_data) or [],
            'cost_categories': cost_categories,
            'resource_utilization': _safe(chart_generator.generate_node_utilization_data, analysis_data) or [],
            'hpa_comparison': _safe(chart_generator.generate_dynamic_hpa_comparison, analysis_data) or [],
            'savings_breakdown': savings,
            'namespace_costs': namespace_costs_result,
            'workload_costs': workload_costs_result,
            'insights': insight_items,
            'trend_data': (_safe(chart_generator.generate_dynamic_trend_data, cluster_id, analysis_data) if cluster_id else None) or [],
            'node_recommendations': node_recs,
            'anomaly_detection': anomaly_data,
            'total_cost': float(analysis_data.get('total_cost', 0) or 0),
            'cpu_gap': float(analysis_data.get('cpu_gap', 0) or 0),
            'memory_gap': float(analysis_data.get('memory_gap', 0) or 0),
            'hpa_efficiency': float(analysis_data.get('hpa_efficiency_percentage', analysis_data.get('hpa_efficiency', 0)) or 0),
            'namespace_count': len(namespace_costs_result),
            'workload_count': sum(1 for w in workload_costs_result if isinstance(w, dict) and w.get('type') == 'Deployment') or len(workload_costs_result),
            'commands_by_category': _safe(chart_generator.generate_execution_commands, analysis_data) or {},
        })
    except Exception as e:
        logger.error(f"Failed to get chart data: {e}", exc_info=True)
        return {
            'cost_breakdown': [], 'cost_categories': [], 'resource_utilization': [], 'hpa_comparison': [],
            'savings_breakdown': {}, 'namespace_costs': [], 'workload_costs': [],
            'insights': [], 'trend_data': [], 'node_recommendations': [],
            'anomaly_detection': {},
            'total_cost': 0, 'cpu_gap': 0, 'memory_gap': 0,
            'hpa_efficiency': 0, 'namespace_count': 0, 'workload_count': 0,
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
            # Override with richer analysis data if available (only override if value > 0)
            cost_val = analysis_data.get('total_cost')
            if cost_val is not None and float(cost_val or 0) > 0:
                overview['total_monthly_cost'] = float(cost_val)
            savings_val = analysis_data.get('total_savings')
            if savings_val is not None and float(savings_val or 0) > 0:
                overview['potential_savings'] = float(savings_val)
            # optimization_score is computed by algorithmic_cost_analyzer (100 - savings%)
            opt_val = analysis_data.get('optimization_score', analysis_data.get('confidence_score'))
            if opt_val is not None and float(opt_val or 0) > 0:
                overview['optimization_score'] = float(opt_val)
            health_val = analysis_data.get('current_health_score')
            overview['health_score'] = float(health_val or 0) if health_val else 0.0
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
