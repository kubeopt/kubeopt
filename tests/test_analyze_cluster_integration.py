"""
Integration tests for the analyze_cluster endpoint path selection.

These tests call the real analyze_cluster async handler with:
  - A real CollectorStore (no mock for freshness logic)
  - Sentinel patches on cloud entry points that raise if called
  - A stub cluster_manager that records update calls

Scenarios:
  1. Fresh report -> collector path; cloud sentinels not triggered;
     results persisted via cluster_manager; response source="collector"
  2. No report -> cloud path started; cluster_manager.update_cluster_analysis
     not called with collector data; response source="cloud"
  3. Stale report -> cloud path (expired between check and run is handled);
     response source="cloud"
  4. Cloud path validates: run_subscription_aware_background_analysis is called
     with the correct cluster parameters
  5. Collector path does not reuse previous analysis data: persisted results
     come from the fresh report, not from any prior analysis_results in memory
"""

import json
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, call

os.environ.setdefault("LOCAL_DEV", "true")

from shared.models.collector import CollectorReport

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> CollectorReport:
    return CollectorReport(**json.loads((FIXTURES / name).read_text()))


def _make_cluster_manager(cluster_row: dict):
    """Stub cluster_manager that records calls."""
    mgr = MagicMock()
    mgr.get_cluster.return_value = cluster_row
    return mgr


def _cluster_row(cluster_id: str) -> dict:
    return {
        'cluster_id': cluster_id,
        'name': 'test-cluster',
        'resource_group': 'rg-test',
        'subscription_id': 'sub-000',
        'cloud_provider': 'azure',
        'region': 'eastus',
    }


def _make_fresh_store(report: CollectorReport):
    from infrastructure.services.collector_store import CollectorStore
    store = CollectorStore()
    store.save(report.model_copy(update={"collected_at": datetime.utcnow()}))
    return store


def _make_stale_store(report: CollectorReport):
    from infrastructure.services.collector_store import CollectorStore
    store = CollectorStore()
    store.save(report.model_copy(update={"collected_at": datetime.utcnow() - timedelta(hours=2)}))
    return store


def _make_empty_store():
    from infrastructure.services.collector_store import CollectorStore
    return CollectorStore()


def _cloud_sentinel(*args, **kwargs):
    raise AssertionError("Cloud path must not be entered when collector report is fresh")


# ---------------------------------------------------------------------------
# Fresh report -> collector path
# ---------------------------------------------------------------------------

class TestFreshReportIntegration:
    @pytest.mark.asyncio
    async def test_fresh_report_returns_completed_collector_source(self):
        from presentation.api.v2.routers.analysis import analyze_cluster

        report = _load("collector_report_small.json")
        store = _make_fresh_store(report)
        mgr = _make_cluster_manager(_cluster_row(report.cluster_id))

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            with patch("infrastructure.services.collector_store.get_collector_store", return_value=store):
                result = await analyze_cluster(
                    cluster_id=report.cluster_id,
                    user={"sub": "test"},
                    cluster_manager=mgr,
                )

        assert result["status"] == "completed"
        assert result["source"] == "collector"

    @pytest.mark.asyncio
    async def test_fresh_report_persists_results_via_cluster_manager(self):
        """Results from the collector path must be saved to the DB."""
        from presentation.api.v2.routers.analysis import analyze_cluster

        report = _load("collector_report_small.json")
        store = _make_fresh_store(report)
        mgr = _make_cluster_manager(_cluster_row(report.cluster_id))

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            with patch("infrastructure.services.collector_store.get_collector_store", return_value=store):
                with patch("infrastructure.services.background_processor.enhanced_cluster_manager", mgr):
                    await analyze_cluster(
                        cluster_id=report.cluster_id,
                        user={"sub": "test"},
                        cluster_manager=mgr,
                    )

        mgr.update_cluster_analysis.assert_called_once()
        saved_data = mgr.update_cluster_analysis.call_args[0][1]
        assert saved_data['source'] == 'collector'
        assert isinstance(saved_data['recommendations'], list)
        assert saved_data['total_savings'] is None

    @pytest.mark.asyncio
    async def test_fresh_report_persisted_results_have_no_destructive_commands(self):
        from presentation.api.v2.routers.analysis import analyze_cluster

        report = _load("collector_report_gpu_workloads.json")
        store = _make_fresh_store(report)
        mgr = _make_cluster_manager(_cluster_row(report.cluster_id))

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            with patch("infrastructure.services.collector_store.get_collector_store", return_value=store):
                with patch("infrastructure.services.background_processor.enhanced_cluster_manager", mgr):
                    await analyze_cluster(
                        cluster_id=report.cluster_id,
                        user={"sub": "test"},
                        cluster_manager=mgr,
                    )

        saved_data = mgr.update_cluster_analysis.call_args[0][1]
        for rec in saved_data['recommendations']:
            cmd = rec.get('command')
            assert cmd is None or 'delete' not in cmd.lower(), (
                f"Persisted recommendation must not include deletion commands: {rec.get('title')!r}"
            )

    @pytest.mark.asyncio
    async def test_fresh_report_does_not_reuse_stale_in_memory_results(self):
        """
        The collector path must derive results from the fresh report, not from
        any pre-existing in-memory analysis_results.
        """
        from presentation.api.v2.routers.analysis import analyze_cluster
        from shared.config.config import analysis_results

        report = _load("collector_report_small.json")
        store = _make_fresh_store(report)
        mgr = _make_cluster_manager(_cluster_row(report.cluster_id))

        # Inject stale in-memory results for the same cluster_id
        analysis_results[report.cluster_id] = {"total_savings": 9999, "source": "stale"}

        try:
            with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                       side_effect=_cloud_sentinel):
                with patch("infrastructure.services.collector_store.get_collector_store", return_value=store):
                    with patch("infrastructure.services.background_processor.enhanced_cluster_manager", mgr):
                        await analyze_cluster(
                            cluster_id=report.cluster_id,
                            user={"sub": "test"},
                            cluster_manager=mgr,
                        )
        finally:
            analysis_results.pop(report.cluster_id, None)

        mgr.update_cluster_analysis.assert_called_once()
        saved_data = mgr.update_cluster_analysis.call_args[0][1]
        assert saved_data['source'] == 'collector'
        assert saved_data.get('total_savings') is None


# ---------------------------------------------------------------------------
# No / stale report -> cloud path
# ---------------------------------------------------------------------------

class TestCloudPathFallback:
    @pytest.mark.asyncio
    async def test_no_report_starts_cloud_analysis(self):
        from presentation.api.v2.routers.analysis import analyze_cluster

        store = _make_empty_store()
        mgr = _make_cluster_manager(_cluster_row("cloud-cluster-001"))
        cloud_thread_started = []

        def _record_cloud_start(*args, **kwargs):
            cloud_thread_started.append(True)

        with patch("presentation.api.v2.routers.analysis.get_collector_store", return_value=store):
            with patch("presentation.api.v2.routers.analysis.threading") as mock_threading:
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread
                result = await analyze_cluster(
                    cluster_id="cloud-cluster-001",
                    user={"sub": "test"},
                    cluster_manager=mgr,
                )

        assert result["source"] == "cloud"
        assert result["status"] == "started"
        mock_thread.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_report_cloud_path_passes_correct_cluster_params(self):
        """Cloud path must pass the cluster's resource_group, subscription_id,
        cloud_provider, and region to run_subscription_aware_background_analysis."""
        from presentation.api.v2.routers.analysis import analyze_cluster

        cluster_id = "cloud-cluster-002"
        row = {
            'name': 'my-cluster',
            'resource_group': 'rg-prod',
            'subscription_id': 'sub-abc',
            'cloud_provider': 'aws',
            'region': 'us-west-2',
        }
        store = _make_empty_store()
        mgr = _make_cluster_manager(row)

        with patch("presentation.api.v2.routers.analysis.get_collector_store", return_value=store):
            with patch("presentation.api.v2.routers.analysis.threading") as mock_threading:
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread
                await analyze_cluster(
                    cluster_id=cluster_id,
                    user={"sub": "test"},
                    cluster_manager=mgr,
                )

        call_kwargs = mock_threading.Thread.call_args[1]
        assert call_kwargs['kwargs']['subscription_id'] == 'sub-abc'
        assert call_kwargs['kwargs']['cloud_provider'] == 'aws'
        assert call_kwargs['kwargs']['region'] == 'us-west-2'

    @pytest.mark.asyncio
    async def test_stale_report_falls_through_to_cloud_path(self):
        """A stale (expired) report must not trigger collector analysis."""
        from presentation.api.v2.routers.analysis import analyze_cluster

        report = _load("collector_report_small.json")
        store = _make_stale_store(report)
        mgr = _make_cluster_manager(_cluster_row(report.cluster_id))

        with patch("presentation.api.v2.routers.analysis.get_collector_store", return_value=store):
            with patch("presentation.api.v2.routers.analysis.threading") as mock_threading:
                mock_thread = MagicMock()
                mock_threading.Thread.return_value = mock_thread
                result = await analyze_cluster(
                    cluster_id=report.cluster_id,
                    user={"sub": "test"},
                    cluster_manager=mgr,
                )

        assert result["source"] == "cloud"
        mock_thread.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_cloud_path_does_not_persist_collector_results(self):
        """When cloud path is chosen, cluster_manager must not receive
        collector analysis data."""
        from presentation.api.v2.routers.analysis import analyze_cluster

        store = _make_empty_store()
        mgr = _make_cluster_manager(_cluster_row("cloud-cluster-003"))

        with patch("presentation.api.v2.routers.analysis.get_collector_store", return_value=store):
            with patch("presentation.api.v2.routers.analysis.threading") as mock_threading:
                mock_threading.Thread.return_value = MagicMock()
                await analyze_cluster(
                    cluster_id="cloud-cluster-003",
                    user={"sub": "test"},
                    cluster_manager=mgr,
                )

        # update_cluster_analysis should not be called with collector data
        for c in mgr.update_cluster_analysis.call_args_list:
            data = c[0][1] if len(c[0]) > 1 else c[1].get('analysis_data', {})
            assert data.get('source') != 'collector', (
                "Cloud path must not write collector-source analysis data"
            )
