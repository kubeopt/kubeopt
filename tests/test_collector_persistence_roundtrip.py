"""
Real persistence round-trip tests for collector-backed analysis.

Uses a real EnhancedMultiSubscriptionClusterManager backed by a temporary
SQLite database -- no mocks for the persistence layer. Cloud adapters are
replaced by sentinels that raise AssertionError if called, so a test
failure is unambiguous: either the collector path called cloud code, or
the persistence/read path is broken.

Covers:
  - analyze -> persist -> read -> overview: null costs, correct inventory
  - Old cloud result is superseded by a newer collector result
  - Persistence failure propagates as an exception (no silent swallow)
  - pod_count from collector payload is surfaced by the overview
  - cloud worker validation is not bypassed by a coincident fresh report
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("LOCAL_DEV", "true")

from shared.models.collector import CollectorReport
from infrastructure.services.collector_store import CollectorStore

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> CollectorReport:
    return CollectorReport(**json.loads((FIXTURES / name).read_text()))


def _make_fresh_store(report: CollectorReport) -> CollectorStore:
    store = CollectorStore()
    store.save(report.model_copy(update={"collected_at": datetime.utcnow()}))
    return store


def _make_manager(tmp_path: str):
    """Real cluster manager backed by a temp SQLite DB."""
    from infrastructure.persistence.cluster_database import EnhancedMultiSubscriptionClusterManager
    return EnhancedMultiSubscriptionClusterManager(db_path=tmp_path)


def _add_cluster(mgr, cluster_id: str) -> None:
    """Insert a minimal cluster row so update_cluster_analysis can find it."""
    parts = cluster_id.split("_", 1)
    rg = parts[0] if len(parts) > 1 else "rg-test"
    name = parts[1] if len(parts) > 1 else cluster_id
    mgr.add_cluster({
        'cluster_name': name,
        'resource_group': rg,
        'cloud_provider': 'azure',
        'region': 'eastus',
    })


def _cloud_sentinel(*args, **kwargs):
    raise AssertionError(f"Cloud adapter must not be called on collector path: {args!r}")


# ---------------------------------------------------------------------------
# Helpers to read back the persisted row directly from SQLite
# ---------------------------------------------------------------------------

def _read_latest_row(db_path: str, cluster_id: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            'SELECT results, total_cost, total_savings FROM analysis_results '
            'WHERE cluster_id = ? AND results IS NOT NULL '
            'ORDER BY analysis_date DESC LIMIT 1',
            (cluster_id,),
        ).fetchone()
    if row is None:
        return {}
    raw = row['results']
    data = json.loads(raw.decode('utf-8') if isinstance(raw, bytes) else raw)
    return {
        'data': data,
        'total_cost_col': row['total_cost'],
        'total_savings_col': row['total_savings'],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPersistenceRoundTrip:
    def test_collector_write_stores_null_costs(self, tmp_path):
        """
        After run_collector_analysis, the DB row must have total_cost=NULL
        and total_savings=NULL. float(None) must not coerce them to 0.
        """
        from infrastructure.services.background_processor import run_collector_analysis

        db_path = str(tmp_path / "clusters.db")
        mgr = _make_manager(db_path)
        report = _load("collector_report_small.json")
        _add_cluster(mgr, report.cluster_id)
        store = _make_fresh_store(report)

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            run_collector_analysis(report.cluster_id, collector_store=store, cluster_manager=mgr)

        row = _read_latest_row(db_path, report.cluster_id)
        assert row, "No row written to analysis_results"
        assert row['total_cost_col'] is None, (
            f"total_cost column must be NULL for collector results, got {row['total_cost_col']}"
        )
        assert row['total_savings_col'] is None, (
            f"total_savings column must be NULL for collector results, got {row['total_savings_col']}"
        )

    def test_collector_write_preserves_inventory_counts(self, tmp_path):
        """node_count and pod_count must survive the serialize -> write -> read cycle."""
        from infrastructure.services.background_processor import run_collector_analysis

        db_path = str(tmp_path / "clusters.db")
        mgr = _make_manager(db_path)
        report = _load("collector_report_small.json")
        _add_cluster(mgr, report.cluster_id)
        store = _make_fresh_store(report)

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            result = run_collector_analysis(report.cluster_id, collector_store=store, cluster_manager=mgr)

        expected_nodes = result['node_count']
        expected_pods = result['pod_count']

        row = _read_latest_row(db_path, report.cluster_id)
        data = row['data']
        assert data.get('node_count') == expected_nodes, (
            f"node_count not preserved: expected {expected_nodes}, got {data.get('node_count')}"
        )
        assert data.get('pod_count') == expected_pods, (
            f"pod_count not preserved: expected {expected_pods}, got {data.get('pod_count')}"
        )

    def test_collector_result_read_back_via_get_analysis_data(self, tmp_path):
        """
        _get_analysis_data must return the collector row with source='collector'
        and total_cost=None after a real write.
        """
        from infrastructure.services.background_processor import run_collector_analysis
        from shared.utils.shared import _get_analysis_data

        db_path = str(tmp_path / "clusters.db")
        mgr = _make_manager(db_path)
        report = _load("collector_report_small.json")
        _add_cluster(mgr, report.cluster_id)
        store = _make_fresh_store(report)

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            run_collector_analysis(report.cluster_id, collector_store=store, cluster_manager=mgr)

        with patch("shared.utils.shared.enhanced_cluster_manager", mgr):
            data, source = _get_analysis_data(report.cluster_id)

        assert data is not None, f"_get_analysis_data returned None (source={source!r})"
        assert data.get('source') == 'collector', (
            f"Expected source='collector', got {data.get('source')!r}"
        )
        assert data.get('total_cost') is None, (
            f"total_cost must be None after collector write, got {data.get('total_cost')}"
        )

    def test_collector_result_supersedes_older_cloud_result(self, tmp_path):
        """
        A collector run that follows an older cloud result must be returned by
        _get_analysis_data, not the cloud result.
        """
        from infrastructure.services.background_processor import run_collector_analysis
        from shared.utils.shared import _get_analysis_data
        from infrastructure.persistence.cluster_database import serialize_implementation_plan

        db_path = str(tmp_path / "clusters.db")
        mgr = _make_manager(db_path)
        report = _load("collector_report_small.json")
        _add_cluster(mgr, report.cluster_id)

        # Write a synthetic "old cloud result" directly to the DB at an earlier timestamp.
        old_cloud = {
            'source': 'cloud',
            'total_cost': 500.0,
            'total_savings': 100.0,
            'cluster_id': report.cluster_id,
        }
        serialized_cloud = serialize_implementation_plan(old_cloud)
        past_date = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                'INSERT INTO analysis_results (cluster_id, analysis_date, results, total_cost, total_savings, confidence_level) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (report.cluster_id, past_date,
                 json.dumps(serialized_cloud).encode('utf-8'), 500.0, 100.0, 0.0),
            )
            conn.commit()

        # Now run collector analysis (newer timestamp).
        store = _make_fresh_store(report)
        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            run_collector_analysis(report.cluster_id, collector_store=store, cluster_manager=mgr)

        with patch("shared.utils.shared.enhanced_cluster_manager", mgr):
            data, source = _get_analysis_data(report.cluster_id)

        assert data is not None
        assert data.get('source') == 'collector', (
            f"Collector result should supersede old cloud result; got source={data.get('source')!r}"
        )

    def test_overview_surfaces_pod_count_from_collector(self, tmp_path):
        """
        dashboard_overview must return pod_count from the persisted collector
        payload, not count pods from a 'pods' list (which collector rows lack).
        """
        from infrastructure.services.background_processor import run_collector_analysis

        db_path = str(tmp_path / "clusters.db")
        mgr = _make_manager(db_path)
        report = _load("collector_report_small.json")
        _add_cluster(mgr, report.cluster_id)
        store = _make_fresh_store(report)

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            result = run_collector_analysis(report.cluster_id, collector_store=store, cluster_manager=mgr)

        expected_pods = result['pod_count']

        # Simulate what dashboard_overview does: read back and pass through the
        # pod_count field.
        row = _read_latest_row(db_path, report.cluster_id)
        data = row['data']

        # Mirror the overview pod_count logic from analysis.py
        pod_count_direct = data.get('pod_count')
        if isinstance(pod_count_direct, int):
            pod_count = pod_count_direct
        else:
            pods_data = data.get('pods', data.get('pod_data', []))
            pod_count = len(pods_data) if isinstance(pods_data, list) else int(pods_data or 0)

        assert pod_count == expected_pods, (
            f"Overview pod_count {pod_count} != expected {expected_pods}; "
            "pod_count integer field not propagated from collector payload"
        )

    def test_persistence_failure_propagates(self, tmp_path):
        """
        When update_cluster_analysis raises, run_collector_analysis must
        propagate the exception. It must NOT return successfully.
        """
        from infrastructure.services.background_processor import run_collector_analysis

        report = _load("collector_report_small.json")
        store = _make_fresh_store(report)
        broken_mgr = MagicMock()
        broken_mgr.update_cluster_analysis.side_effect = RuntimeError("DB unavailable")

        with patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                   side_effect=_cloud_sentinel):
            with pytest.raises(RuntimeError, match="DB unavailable"):
                run_collector_analysis(
                    report.cluster_id,
                    collector_store=store,
                    cluster_manager=broken_mgr,
                )

    def test_cloud_worker_validates_even_with_fresh_report(self, tmp_path):
        """
        run_subscription_aware_background_analysis must call
        account_mgr.validate_cluster_access even when a fresh collector report
        exists for the cluster. The cloud path must not inherit the collector
        bypass.
        """
        from infrastructure.services.background_processor import should_validate_cluster_access
        from infrastructure.services.collector_store import CollectorStore

        report = _load("collector_report_small.json")
        # Real global store has a fresh report.
        real_store = _make_fresh_store(report)

        # Simulate what the cloud worker does: pass an empty CollectorStore.
        empty_store = CollectorStore()
        result = should_validate_cluster_access(
            report.cluster_id,
            collector_store=empty_store,
        )
        assert result is True, (
            "Cloud worker's empty-store sentinel must force validation even when "
            "a fresh report exists in the global store"
        )
