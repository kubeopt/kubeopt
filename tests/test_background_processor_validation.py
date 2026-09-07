from infrastructure.services import background_processor as bp


class StubClusterManager:
    def __init__(self, latest=None):
        self.latest = latest
        self.status_updates = []
        self.session_updates = []

    def get_latest_analysis(self, cluster_id):
        return self.latest

    def update_analysis_status(self, *args):
        self.status_updates.append(args)

    def update_subscription_analysis_session(self, *args):
        self.session_updates.append(args)


class StubCollectorStore:
    def has_fresh_report(self, cluster_id):
        return False


def test_should_not_validate_when_saved_analysis_exists(monkeypatch):
    manager = StubClusterManager(latest={"total_cost": 43.01})

    assert bp.should_validate_cluster_access(
        "rg_cluster",
        collector_store=StubCollectorStore(),
        cluster_manager=manager,
        results={},
    ) is False


def test_should_validate_when_no_collector_or_saved_analysis():
    manager = StubClusterManager(latest=None)

    assert bp.should_validate_cluster_access(
        "brand_new_cluster",
        collector_store=StubCollectorStore(),
        cluster_manager=manager,
        results={},
    ) is True


def test_complete_with_existing_analysis_marks_success(monkeypatch):
    manager = StubClusterManager(latest={
        "total_cost": 43.01,
        "total_savings": 11.72,
        "analysis_confidence": 0.91,
    })
    monkeypatch.setattr(bp, "enhanced_cluster_manager", manager)
    monkeypatch.setitem(bp.analysis_status_tracker, "rg_cluster", {})

    completed = bp._complete_with_existing_analysis(
        "rg_cluster",
        "sub-123",
        "production-sub",
        "session-1",
        "cloud subscription unavailable",
    )

    assert completed is True
    assert manager.status_updates[0][:3] == (
        "rg_cluster",
        "completed",
        100,
    )
    assert bp.analysis_status_tracker["rg_cluster"]["status"] == "completed"
    assert bp.analysis_status_tracker["rg_cluster"]["progress"] == 100
    assert bp.analysis_status_tracker["rg_cluster"]["results"]["total_cost"] == 43.01
