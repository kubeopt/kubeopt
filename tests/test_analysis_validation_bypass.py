from infrastructure.services.background_processor import should_validate_cluster_access


class FakeCollectorStore:
    def __init__(self, fresh: bool = False):
        self.fresh = fresh

    def has_fresh_report(self, cluster_id: str) -> bool:
        return self.fresh


def test_skips_cloud_validation_when_fresh_collector_report_exists():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(fresh=True),
    ) is False


def test_requires_cloud_validation_when_no_collector_report():
    assert should_validate_cluster_access(
        "cluster-1",
        collector_store=FakeCollectorStore(fresh=False),
    ) is True


def test_requires_cloud_validation_for_unknown_cluster():
    assert should_validate_cluster_access(
        "new-cluster",
        collector_store=FakeCollectorStore(fresh=False),
    ) is True
