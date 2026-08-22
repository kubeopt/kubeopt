from infrastructure.services.background_processor import should_validate_cluster_access
from typing import Optional


class FakeCollectorStore:
    def __init__(self, fresh: bool = False):
        self.fresh = fresh

    def has_fresh_report(self, cluster_id: str) -> bool:
        return self.fresh


class FakeClusterManager:
    def __init__(self, latest_analysis=None, error: Optional[Exception] = None):
        self.latest_analysis = latest_analysis
        self.error = error

    def get_latest_analysis(self, cluster_id: str):
        if self.error:
            raise self.error
        return self.latest_analysis


def test_skips_cloud_validation_when_fresh_collector_report_exists():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(fresh=True),
        cluster_manager=FakeClusterManager(),
        results={},
    ) is False


def test_skips_cloud_validation_when_in_memory_results_exist():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(),
        cluster_manager=FakeClusterManager(),
        results={"cluster-1": {"total_cost": 42}},
    ) is False


def test_skips_cloud_validation_when_persisted_analysis_exists():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(),
        cluster_manager=FakeClusterManager(latest_analysis={"total_cost": 42}),
        results={},
    ) is False


def test_requires_cloud_validation_for_unknown_cluster():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(),
        cluster_manager=FakeClusterManager(),
        results={},
    ) is True


def test_requires_cloud_validation_when_persisted_analysis_check_fails():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(),
        cluster_manager=FakeClusterManager(error=RuntimeError("db unavailable")),
        results={},
    ) is True
