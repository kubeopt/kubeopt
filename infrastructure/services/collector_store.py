"""
In-memory store for the latest CollectorReport per cluster.

Kept in-memory for now -- reports are pushed frequently (every 5 min)
and are ephemeral by nature. A database layer can be added later if
historical trend data becomes a product requirement.
"""

import threading
from typing import Optional

from shared.models.collector import CollectorReport


class CollectorStore:
    def __init__(self, max_age_seconds: int = 600):
        self._reports: dict[str, CollectorReport] = {}
        self._lock = threading.Lock()
        self._max_age_seconds = max_age_seconds

    def save(self, report: CollectorReport) -> None:
        with self._lock:
            self._reports[report.cluster_id] = report

    def get(self, cluster_id: str) -> Optional[CollectorReport]:
        with self._lock:
            return self._reports.get(cluster_id)

    def has_fresh_report(self, cluster_id: str) -> bool:
        report = self.get(cluster_id)
        if report is None:
            return False
        return report.is_fresh(self._max_age_seconds)


# Module-level singleton shared across the process
_store = CollectorStore()


def get_collector_store() -> CollectorStore:
    return _store
