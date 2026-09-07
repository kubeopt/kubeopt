"""Tests for the native in-cluster collector -- schema, storage, and API endpoint."""

import json
import os
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("LOCAL_DEV", "true")

from shared.models.collector import (
    CollectorReport, NodeSummary, PodSummary, HPASummary,
    PVCSummary, ServiceSummary, NamespaceSummary,
)


FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestCollectorReportSchema:
    def test_minimal_report(self):
        r = CollectorReport(cluster_id="c1")
        assert r.cluster_id == "c1"
        assert r.total_nodes == 0
        assert r.metrics_server_available is False
        assert r.metrics_server_error is None
        assert isinstance(r.collected_at, datetime)

    def test_is_fresh_when_just_collected(self):
        r = CollectorReport(cluster_id="c1")
        assert r.is_fresh() is True

    def test_is_fresh_accepts_timezone_aware_collector_timestamp(self):
        collected_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        r = CollectorReport(cluster_id="c1", collected_at=collected_at)
        assert r.is_fresh() is True

    def test_is_stale_when_old(self):
        old = datetime.utcnow() - timedelta(seconds=700)
        r = CollectorReport(cluster_id="c1", collected_at=old)
        assert r.is_fresh() is False

    def test_custom_freshness_window(self):
        five_min_ago = datetime.utcnow() - timedelta(seconds=300)
        r = CollectorReport(cluster_id="c1", collected_at=five_min_ago)
        assert r.is_fresh(max_age_seconds=400) is True
        assert r.is_fresh(max_age_seconds=200) is False

    def test_node_summary_defaults(self):
        n = NodeSummary(name="node-1")
        assert n.ready is True
        assert n.cpu_used_m is None   # metrics-server may be absent

    def test_pod_summary_defaults(self):
        p = PodSummary(name="pod-1", namespace="prod")
        assert p.phase == "Running"
        assert p.cpu_used_m is None

    def test_full_report_roundtrip(self):
        report = CollectorReport(
            cluster_id="c1",
            nodes=[NodeSummary(name="n1", cpu_allocatable_m=4000)],
            pods=[PodSummary(name="p1", namespace="prod", cpu_request_m=500)],
            hpas=[HPASummary(
                name="h1", namespace="prod", target_kind="Deployment",
                target_name="svc", min_replicas=1, max_replicas=5,
                current_replicas=1, desired_replicas=1,
            )],
            pvcs=[PVCSummary(name="pvc1", namespace="prod", capacity_gb=50.0)],
            services=[ServiceSummary(name="svc-lb", namespace="prod", type="LoadBalancer")],
            namespaces=[NamespaceSummary(name="prod", pod_count=1)],
            total_nodes=1,
            total_pods=1,
            metrics_server_available=True,
        )
        dumped = report.model_dump()
        restored = CollectorReport(**dumped)
        assert restored.cluster_id == "c1"
        assert restored.nodes[0].name == "n1"
        assert restored.pods[0].cpu_request_m == 500


# ---------------------------------------------------------------------------
# Fixture loading tests
# ---------------------------------------------------------------------------

class TestCollectorFixtures:
    @pytest.mark.parametrize("fixture_name", [
        "collector_report_small.json",
        "collector_report_idle_namespace.json",
        "collector_report_hpa_missing.json",
    ])
    def test_fixture_parses_cleanly(self, fixture_name):
        data = json.loads((FIXTURES / fixture_name).read_text())
        report = CollectorReport(**data)
        assert report.cluster_id
        assert isinstance(report.collected_at, datetime)

    def test_small_fixture_has_expected_shape(self):
        data = json.loads((FIXTURES / "collector_report_small.json").read_text())
        r = CollectorReport(**data)
        assert r.total_nodes == 2
        assert r.total_pods == 4
        assert len(r.nodes) == 2
        assert len(r.hpas) == 1
        assert r.hpas[0].name == "api-server-hpa"
        assert len(r.services) == 2
        assert any(s.type == "LoadBalancer" for s in r.services)

    def test_idle_namespace_fixture_has_low_usage_dev_ns(self):
        data = json.loads((FIXTURES / "collector_report_idle_namespace.json").read_text())
        r = CollectorReport(**data)
        dev_ns = next(ns for ns in r.namespaces if ns.name == "dev")
        assert dev_ns.cpu_used_m is not None
        # dev namespace: 4 pods, ~14m used out of 500m requested = very idle
        assert dev_ns.cpu_used_m < 30

    def test_hpa_missing_fixture_has_no_hpas(self):
        data = json.loads((FIXTURES / "collector_report_hpa_missing.json").read_text())
        r = CollectorReport(**data)
        assert r.hpas == []
        assert r.metrics_server_available is False
        # live usage should be null when metrics-server absent
        for pod in r.pods:
            assert pod.cpu_used_m is None

    def test_report_preserves_metrics_server_error_reason(self):
        r = CollectorReport(
            cluster_id="c1",
            metrics_server_available=False,
            metrics_server_error="rbac_denied",
        )
        dumped = r.model_dump()
        restored = CollectorReport(**dumped)
        assert restored.metrics_server_error == "rbac_denied"


# ---------------------------------------------------------------------------
# CollectorStore tests
# ---------------------------------------------------------------------------

class TestCollectorStore:
    def test_store_and_retrieve(self):
        from infrastructure.services.collector_store import CollectorStore
        store = CollectorStore()
        report = CollectorReport(cluster_id="c1", total_nodes=3)
        store.save(report)
        retrieved = store.get("c1")
        assert retrieved is not None
        assert retrieved.total_nodes == 3

    def test_get_returns_none_for_unknown_cluster(self):
        from infrastructure.services.collector_store import CollectorStore
        store = CollectorStore()
        assert store.get("nonexistent") is None

    def test_latest_report_overwrites_previous(self):
        from infrastructure.services.collector_store import CollectorStore
        store = CollectorStore()
        store.save(CollectorReport(cluster_id="c1", total_nodes=1))
        store.save(CollectorReport(cluster_id="c1", total_nodes=5))
        assert store.get("c1").total_nodes == 5

    def test_has_fresh_report(self):
        from infrastructure.services.collector_store import CollectorStore
        store = CollectorStore()
        store.save(CollectorReport(cluster_id="c1"))
        assert store.has_fresh_report("c1") is True
        assert store.has_fresh_report("other") is False

    def test_stale_report_not_fresh(self):
        from infrastructure.services.collector_store import CollectorStore
        store = CollectorStore()
        old = datetime.utcnow() - timedelta(seconds=700)
        store.save(CollectorReport(cluster_id="c1", collected_at=old))
        assert store.has_fresh_report("c1") is False


# ---------------------------------------------------------------------------
# Analysis preference tests
# ---------------------------------------------------------------------------

class TestCollectorPreference:
    def test_prefers_fresh_collector_over_provider_path(self):
        from infrastructure.services.collector_store import CollectorStore
        from infrastructure.services.analysis_source import get_data_source, DataSource

        store = CollectorStore()
        store.save(CollectorReport(cluster_id="c1", total_nodes=2))
        source = get_data_source("c1", store)
        assert source == DataSource.COLLECTOR

    def test_falls_back_to_provider_when_no_report(self):
        from infrastructure.services.collector_store import CollectorStore
        from infrastructure.services.analysis_source import get_data_source, DataSource

        store = CollectorStore()
        source = get_data_source("unknown-cluster", store)
        assert source == DataSource.PROVIDER

    def test_falls_back_to_provider_when_report_stale(self):
        from infrastructure.services.collector_store import CollectorStore
        from infrastructure.services.analysis_source import get_data_source, DataSource

        store = CollectorStore()
        old = datetime.utcnow() - timedelta(seconds=700)
        store.save(CollectorReport(cluster_id="c1", collected_at=old))
        source = get_data_source("c1", store)
        assert source == DataSource.PROVIDER


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestCollectorAPI:
    @pytest.mark.asyncio
    async def test_get_collector_report_accepts_timezone_aware_timestamp(self):
        from infrastructure.services.collector_store import get_collector_store
        from presentation.api.v2.routers.collector import get_collector_report

        report = CollectorReport(
            cluster_id="tz-aware-cluster",
            collected_at=datetime.now(timezone.utc),
            total_nodes=1,
            total_pods=9,
            metrics_server_available=False,
            metrics_server_error="network_unreachable",
        )
        get_collector_store().save(report)

        response = await get_collector_report("tz-aware-cluster", user={"sub": "test"})

        assert response["cluster_id"] == "tz-aware-cluster"
        assert response["is_fresh"] is True
        assert response["nodes"] == 1
        assert response["pods"] == 9
        assert response["metrics_server_available"] is False
        assert response["metrics_server_error"] == "network_unreachable"
