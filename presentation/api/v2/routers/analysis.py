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
from presentation.api.v2.schemas.analysis import ChartDataResponse, CPUOptimizationPlan, RecommendationSchema
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import (
    get_cluster_manager, get_cpu_report_exporter,
    get_analysis_results, get_analysis_cache,
)
from assessment.command_generator import generate_recommendations
from assessment.gpu_evaluator import evaluate_gpu_workloads
from infrastructure.services.collector_store import get_collector_store
from infrastructure.demo.demo_data import (
    is_demo_mode, get_demo_cluster, get_demo_analysis_status, get_demo_chart_data,
    get_demo_recommendations,
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

# Titles produced exclusively by CPU-proxy GPU rules that have been disabled.
# Rules 1 (idle pod) and 4 (low occupancy) used CPU utilisation as a proxy for
# GPU idleness, which is invalid for inference/serving workloads. Findings with
# these titles are filtered from all API responses so stale DB records cannot
# surface after the rules were disabled.
_DISABLED_GPU_RULE_TITLES: frozenset[str] = frozenset({
    "Idle GPU pod",              # rule 1 original title
    "Low CPU on GPU pod",        # rule 1 intermediate title during fix
    "Low GPU node pool occupancy",  # rule 4
})


def _filter_disabled_gpu_findings(recommendations: list[dict]) -> list[dict]:
    """Remove stale findings from disabled CPU-proxy GPU rules by stable title prefix."""
    return [
        r for r in recommendations
        if not any(r.get("title", "").startswith(t) for t in _DISABLED_GPU_RULE_TITLES)
    ]


def _append_collector_gpu_recommendations(cluster_id: str, recommendations: list[dict]) -> list[dict]:
    """Append deterministic GPU recommendations from the latest collector report."""
    report = get_collector_store().get(cluster_id)
    if report is None:
        return recommendations

    gpu_recommendations = [r.model_dump() for r in evaluate_gpu_workloads(report)]
    if not gpu_recommendations:
        return recommendations

    existing_ids = {r.get("id") for r in recommendations if isinstance(r, dict)}
    recommendations.extend(r for r in gpu_recommendations if r.get("id") not in existing_ids)
    recommendations.sort(key=lambda r: (-float(r.get("priority_score", 0) or 0), str(r.get("id", ""))))
    return recommendations


@router.post("/clusters/{cluster_id:path}/analyze")
async def analyze_cluster(
    cluster_id: str,
    source: Optional[str] = Query(None, description="Analysis source: 'collector' or 'cloud'. "
                                  "When omitted the route auto-selects: collector if a fresh "
                                  "report is present, otherwise cloud."),
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Trigger analysis for a cluster. Returns session key for progress tracking.

    source='collector': requires a fresh in-cluster CollectorReport; returns 422
      if no fresh report exists. Never falls through to cloud.
    source='cloud': always runs cloud-validated analysis; ignores any collector report.
    source omitted: auto-selects collector when a fresh report is present, else cloud.
    """
    if is_demo_mode() and get_demo_cluster(cluster_id):
        return {"session_key": cluster_id, "status": "completed", "message": "Demo analysis ready"}

    try:
        from infrastructure.services.background_processor import (
            run_subscription_aware_background_analysis,
            run_collector_analysis,
            StaleReportError,
        )

        cluster_info = cluster_manager.get_cluster(cluster_id)
        if not cluster_info:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        use_collector = False
        if source == 'collector':
            use_collector = True
        elif source == 'cloud':
            use_collector = False
        else:
            # Auto-select: prefer collector when a fresh report is available.
            collector_store = get_collector_store()
            use_collector = collector_store.has_fresh_report(cluster_id)

        if use_collector:
            # Collector path: no cloud calls. StaleReportError propagates as 422
            # so the caller knows explicitly that the report is stale or absent.
            try:
                run_collector_analysis(
                    cluster_id,
                    collector_store=get_collector_store(),
                    cluster_manager=cluster_manager,
                )
            except StaleReportError as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Collector report not available: {e}",
                )
            return {
                "session_key": cluster_id,
                "status": "completed",
                "source": "collector",
                "message": "Collector-backed analysis completed",
            }

        # Cloud path: validate credentials and run subscription-aware analysis.
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
            "source": "cloud",
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
    if is_demo_mode() and get_demo_cluster(cluster_id):
        return AnalysisStatus(**get_demo_analysis_status(cluster_id))

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

        if is_demo_mode() and cluster_id:
            demo_charts = get_demo_chart_data(cluster_id)
            if demo_charts:
                return {**demo_charts, 'anomaly_detection': {}}

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

        # Extract anomaly detection data — check enhanced_analysis_input first, then top-level
        anomaly_data = {}
        try:
            raw_anomaly = None
            # Primary source: enhanced_analysis_input (where analysis_engine stores it)
            eai_for_anomaly = analysis_data.get('enhanced_analysis_input', {})
            if isinstance(eai_for_anomaly, dict):
                raw_anomaly = eai_for_anomaly.get('anomaly_detection', {})
            # Fallback: top-level analysis_data
            if not raw_anomaly or not isinstance(raw_anomaly, dict) or raw_anomaly.get('total_anomalies', 0) == 0:
                raw_anomaly = analysis_data.get('anomaly_detection', {})
            if isinstance(raw_anomaly, dict) and raw_anomaly.get('total_anomalies', 0) > 0:
                anomaly_data = {
                    'total_anomalies': raw_anomaly.get('total_anomalies', 0),
                    'average_severity': raw_anomaly.get('average_severity', 0),
                    'highest_severity': raw_anomaly.get('highest_severity', 0),
                    'categories': raw_anomaly.get('anomaly_categories', {}),
                    'anomalies': (raw_anomaly.get('anomalies', []) or [])[:10],
                    'detection_type': raw_anomaly.get('detection_type', 'unknown'),
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
            other_keys = ['secrets_management_cost', 'application_services_cost', 'data_services_cost',
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
            'workload_count': len(workload_costs_result),
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
            _last_cost = cluster_info.get('last_cost')
            _last_savings = cluster_info.get('last_savings')
            # Preserve None: a NULL last_cost means pricing is unknown (collector result).
            # Do not substitute 0 -- the UI renders None as "Unavailable".
            overview['total_monthly_cost'] = None if _last_cost is None else float(_last_cost or 0)
            overview['potential_savings'] = None if _last_savings is None else float(_last_savings or 0)
            overview['optimization_score'] = float(cluster_info.get('last_confidence', 0) or 0)

        if analysis_data:
            # Override with richer analysis data if available. For cost: only
            # override when a concrete value exists; None means unknown pricing
            # and must be passed through so the UI can render "Unavailable".
            cost_val = analysis_data.get('total_cost')
            if 'total_cost' in analysis_data:
                if cost_val is not None and float(cost_val or 0) > 0:
                    overview['total_monthly_cost'] = float(cost_val)
                elif cost_val is None:
                    overview['total_monthly_cost'] = None
            # Recompute savings from the FULL recommendations list only.
            # top_recommendations is a truncated display list and cannot establish a total.
            # Rules:
            #   empty after filtering  -> 0.0  (confirmed: no active findings)
            #   non-empty, all None    -> None (unknown: no pricing source available)
            #   non-empty, some values -> sum of non-None values
            # Falls back to stored aggregate only when the full list is absent entirely.
            stored_recs = analysis_data.get('recommendations')
            if isinstance(stored_recs, list):
                active_recs = _filter_disabled_gpu_findings(stored_recs)
                if not active_recs:
                    overview['potential_savings'] = 0.0
                else:
                    known = [
                        float(r['monthly_savings'])
                        for r in active_recs
                        if isinstance(r, dict) and r.get('monthly_savings') is not None
                    ]
                    overview['potential_savings'] = sum(known) if known else None
            else:
                # No full recommendations list; stored aggregate is all we have
                savings_val = analysis_data.get('total_savings')
                if savings_val is not None:
                    overview['potential_savings'] = float(savings_val or 0)
            # optimization_score is computed by algorithmic_cost_analyzer (100 - savings%)
            opt_val = analysis_data.get('optimization_score', analysis_data.get('confidence_score'))
            if opt_val is not None and float(opt_val or 0) > 0:
                overview['optimization_score'] = float(opt_val)
            health_val = analysis_data.get('current_health_score')
            overview['health_score'] = float(health_val or 0) if health_val else 0.0
            overview['node_count'] = int(analysis_data.get('current_node_count', analysis_data.get('node_count', 0)) or 0)
            # Count pods. Collector results store the integer directly; cloud
            # results store the pod list under 'pods' or 'pod_data'.
            pod_count_direct = analysis_data.get('pod_count')
            if isinstance(pod_count_direct, int):
                overview['pod_count'] = pod_count_direct
            else:
                pods_data = analysis_data.get('pods', analysis_data.get('pod_data', []))
                if isinstance(pods_data, list):
                    overview['pod_count'] = len(pods_data)
                elif isinstance(pods_data, int):
                    overview['pod_count'] = pods_data
            # Top recommendations: display from full list when present, top list otherwise
            display_recs = stored_recs if isinstance(stored_recs, list) else analysis_data.get('top_recommendations')
            if isinstance(display_recs, list):
                overview['top_recommendations'] = _filter_disabled_gpu_findings(display_recs)[:5]

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


@router.get("/clusters/{cluster_id:path}/recommendations", response_model=list[RecommendationSchema])
async def get_recommendations(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Return deterministic recommendations for a cluster. No AI required."""
    if is_demo_mode():
        demo = get_demo_cluster(cluster_id)
        if demo:
            return get_demo_recommendations(cluster_id)
        raise HTTPException(status_code=404, detail="Cluster not found")

    cluster = cluster_manager.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    analysis_data = cluster.get("analysis_data") or {}
    if "recommendations" in analysis_data:
        recs = _filter_disabled_gpu_findings(list(analysis_data["recommendations"]))
        return _append_collector_gpu_recommendations(cluster_id, recs)
    recommendations = _filter_disabled_gpu_findings(
        [r.model_dump() for r in generate_recommendations(analysis_data)]
    )
    return _append_collector_gpu_recommendations(cluster_id, recommendations)


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
