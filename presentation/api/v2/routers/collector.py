"""Collector report ingestion endpoint."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import ValidationError

from shared.models.collector import CollectorReport
from infrastructure.services.collector_store import get_collector_store
from infrastructure.services.analysis_source import get_data_source, DataSource
from presentation.api.v2.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/collector", tags=["collector"])


@router.post("/report")
async def ingest_collector_report(
    report: CollectorReport,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Accept a CollectorReport pushed by the in-cluster KubeOpt collector.
    Stores the latest report per cluster_id; analysis engine prefers this
    over the cloud-provider command path when the report is fresh.
    """
    store = get_collector_store()
    store.save(report)
    logger.info(
        "collector report ingested: cluster=%s nodes=%d pods=%d metrics=%s",
        report.cluster_id,
        report.total_nodes,
        report.total_pods,
        report.metrics_server_available,
    )
    return {
        "status": "accepted",
        "cluster_id": report.cluster_id,
        "collected_at": report.collected_at.isoformat(),
        "nodes": report.total_nodes,
        "pods": report.total_pods,
    }


@router.get("/report/{cluster_id}")
async def get_collector_report(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Return the latest collector report for a cluster, if any."""
    store = get_collector_store()
    report = store.get(cluster_id)
    if report is None:
        raise HTTPException(status_code=404, detail="No collector report for this cluster")
    return {
        "cluster_id": report.cluster_id,
        "collected_at": report.collected_at.isoformat(),
        "is_fresh": report.is_fresh(),
        "data_source": get_data_source(cluster_id, store).value,
        "nodes": report.total_nodes,
        "pods": report.total_pods,
        "metrics_server_available": report.metrics_server_available,
    }
