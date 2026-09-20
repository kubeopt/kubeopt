"""
Tests for select_analysis_path and should_validate_cluster_access.

Design rules enforced:
1. Fresh collector report -> CollectorAnalysisService; cloud entry points must
   not be called (verified by raising sentinels, not by inspecting sys.modules).
2. Stale / absent report -> StaleReportError raised before any cloud call.
3. Historical results and previous analyses cannot bypass cloud validation.
4. Fetch-once: the report used for the freshness check is the same snapshot
   passed to the service (a single get() call, no second fetch).
5. Returned recommendations carry no destructive commands and no fabricated savings.
"""

import json
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("LOCAL_DEV", "true")

from shared.models.collector import CollectorReport

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> CollectorReport:
    return CollectorReport(**json.loads((FIXTURES / name).read_text()))


def _fresh_store(report: CollectorReport):
    from infrastructure.services.collector_store import CollectorStore
    store = CollectorStore()
    store.save(report.model_copy(update={"collected_at": datetime.utcnow()}))
    return store


def _stale_store(report: CollectorReport):
    from infrastructure.services.collector_store import CollectorStore
    store = CollectorStore()
    store.save(report.model_copy(update={"collected_at": datetime.utcnow() - timedelta(hours=2)}))
    return store


def _empty_store():
    from infrastructure.services.collector_store import CollectorStore
    return CollectorStore()


# ---------------------------------------------------------------------------
# Fresh report -> collector path (cloud entry points must not be called)
# ---------------------------------------------------------------------------

class TestFreshReportPath:
    def test_fresh_report_returns_collector_source(self):
        from infrastructure.services.background_processor import select_analysis_path
        report = _load("collector_report_small.json")
        result = select_analysis_path(report.cluster_id, collector_store=_fresh_store(report))
        assert result['source'] == 'collector'
        assert result['cluster_id'] == report.cluster_id
        assert isinstance(result['recommendations'], list)
        assert 'report_collected_at' in result

    def test_fresh_report_does_not_call_cloud_adapters(self):
        """
        Run the real collector path with cloud entry points replaced by sentinels
        that raise if called. Unlike sys.modules diffing, this catches lazy/deferred
        imports and avoids false passes when modules are already loaded.
        """
        from infrastructure.services.background_processor import select_analysis_path

        def _raise_if_called(*a, **kw):
            raise AssertionError("Cloud adapter called on collector path")

        report = _load("collector_report_small.json")
        store = _fresh_store(report)

        with (
            patch("infrastructure.services.background_processor.run_subscription_aware_background_analysis",
                  side_effect=_raise_if_called, create=True),
            patch("infrastructure.cloud_providers.azure.accounts.AzureAccountAdapter",
                  side_effect=_raise_if_called, create=True),
            patch("infrastructure.cloud_providers.aws.accounts.AWSAccountManager",
                  side_effect=_raise_if_called, create=True),
            patch("infrastructure.cloud_providers.gcp.accounts.GCPAccountManager",
                  side_effect=_raise_if_called, create=True),
        ):
            result = select_analysis_path(report.cluster_id, collector_store=store)

        assert result['source'] == 'collector'

    def test_fresh_report_recommendations_have_no_destructive_commands(self):
        from infrastructure.services.background_processor import select_analysis_path
        report = _load("collector_report_gpu_workloads.json")
        result = select_analysis_path(report.cluster_id, collector_store=_fresh_store(report))
        for rec in result['recommendations']:
            cmd = rec.get('command')
            assert cmd is None or 'delete' not in cmd.lower(), (
                f"Collector path must not produce deletion commands: "
                f"{rec.get('title')!r} -> {cmd!r}"
            )

    def test_fresh_report_recommendations_have_no_fabricated_savings(self):
        from infrastructure.services.background_processor import select_analysis_path
        report = _load("collector_report_small.json")
        result = select_analysis_path(report.cluster_id, collector_store=_fresh_store(report))
        for rec in result['recommendations']:
            assert rec.get('monthly_savings') is None, (
                f"Collector path must not fabricate savings: "
                f"{rec.get('title')!r} -> {rec.get('monthly_savings')}"
            )

    def test_fetch_once_report_is_used_for_both_freshness_and_analysis(self):
        """
        The report used for the freshness check must be the same snapshot that
        is passed to the service. Verify by patching get() to return one
        specific report and confirming the result reflects that report's cluster_id.
        """
        from infrastructure.services.background_processor import select_analysis_path
        from infrastructure.services.collector_store import CollectorStore

        report = _load("collector_report_small.json")
        fresh = report.model_copy(update={"collected_at": datetime.utcnow()})

        store = CollectorStore()
        get_calls = []

        original_get = store.get

        def _tracked_get(cluster_id):
            result = original_get(cluster_id)
            get_calls.append(cluster_id)
            return result

        store.save(fresh)
        store.get = _tracked_get

        result = select_analysis_path(fresh.cluster_id, collector_store=store)

        assert get_calls.count(fresh.cluster_id) == 1, (
            f"get() must be called exactly once (fetch-once contract); "
            f"called {get_calls.count(fresh.cluster_id)} times"
        )
        assert result['cluster_id'] == fresh.cluster_id


# ---------------------------------------------------------------------------
# Stale / absent report -> StaleReportError (cloud must not be called)
# ---------------------------------------------------------------------------

class TestStaleReportContract:
    def test_stale_report_raises_stale_report_error(self):
        from infrastructure.services.background_processor import select_analysis_path, StaleReportError
        report = _load("collector_report_small.json")
        with pytest.raises(StaleReportError):
            select_analysis_path(report.cluster_id, collector_store=_stale_store(report))

    def test_absent_report_raises_stale_report_error(self):
        from infrastructure.services.background_processor import select_analysis_path, StaleReportError
        with pytest.raises(StaleReportError):
            select_analysis_path("no-such-cluster", collector_store=_empty_store())

    def test_stale_report_error_message_is_actionable(self):
        from infrastructure.services.background_processor import select_analysis_path, StaleReportError
        report = _load("collector_report_small.json")
        with pytest.raises(StaleReportError) as exc_info:
            select_analysis_path(report.cluster_id, collector_store=_stale_store(report))
        msg = str(exc_info.value).lower()
        assert "fresh" in msg or "stale" in msg or "cloud" in msg

    def test_stale_report_does_not_call_cloud_adapters(self):
        """
        StaleReportError must be raised before any cloud adapter is instantiated.
        Verified with sentinels that raise if called.
        """
        from infrastructure.services.background_processor import select_analysis_path, StaleReportError

        def _raise_if_called(*a, **kw):
            raise AssertionError("Cloud adapter called on stale report path")

        report = _load("collector_report_small.json")
        store = _stale_store(report)

        with (
            patch("infrastructure.cloud_providers.azure.accounts.AzureAccountAdapter",
                  side_effect=_raise_if_called, create=True),
            patch("infrastructure.cloud_providers.aws.accounts.AWSAccountManager",
                  side_effect=_raise_if_called, create=True),
            patch("infrastructure.cloud_providers.gcp.accounts.GCPAccountManager",
                  side_effect=_raise_if_called, create=True),
        ):
            with pytest.raises(StaleReportError):
                select_analysis_path(report.cluster_id, collector_store=store)


# ---------------------------------------------------------------------------
# Validation bypass regression
# ---------------------------------------------------------------------------

class TestValidationBypassRegression:
    """
    Regression: should_validate_cluster_access() previously allowed historical
    in-memory results and previous DB analyses to skip cloud validation.
    Both bypasses were rejected. These tests prove they no longer exist.
    """

    def test_in_memory_results_do_not_bypass_validation(self):
        """
        Even when in-memory analysis_results contains the cluster_id, validation
        must be required (fresh collector report is the only bypass).
        """
        from infrastructure.services.background_processor import should_validate_cluster_access
        report = _load("collector_report_small.json")
        stale_store = _stale_store(report)

        # Provide a non-empty in-memory results dict containing the cluster_id
        fake_results = {report.cluster_id: {"total_savings": 500}}
        assert should_validate_cluster_access(
            report.cluster_id,
            collector_store=stale_store,
            results=fake_results,
        ) is True, (
            "In-memory results must not bypass cloud validation"
        )

    def test_previous_db_analysis_does_not_bypass_validation(self):
        """
        Even when a previous analysis exists in the DB, validation must be
        required when no fresh collector report is present.
        """
        from infrastructure.services.background_processor import should_validate_cluster_access
        report = _load("collector_report_small.json")
        stale_store = _stale_store(report)

        # Provide a cluster_manager that claims a previous analysis exists
        class FakeClusterManager:
            def get_latest_analysis(self, cluster_id):
                return {"total_savings": 500, "cluster_id": cluster_id}

        assert should_validate_cluster_access(
            report.cluster_id,
            collector_store=stale_store,
            cluster_manager=FakeClusterManager(),
        ) is True, (
            "Previous DB analysis must not bypass cloud validation"
        )

    def test_fresh_collector_report_bypasses_validation(self):
        """Fresh report is the only legitimate bypass."""
        from infrastructure.services.background_processor import should_validate_cluster_access
        report = _load("collector_report_small.json")
        assert should_validate_cluster_access(
            report.cluster_id,
            collector_store=_fresh_store(report),
        ) is False

    def test_stale_collector_report_requires_validation(self):
        """A stale report must not bypass validation."""
        from infrastructure.services.background_processor import should_validate_cluster_access
        report = _load("collector_report_small.json")
        assert should_validate_cluster_access(
            report.cluster_id,
            collector_store=_stale_store(report),
        ) is True
