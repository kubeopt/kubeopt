"""
Data source selection for analysis.

Determines whether to use fresh collector data (in-cluster push)
or fall back to the existing cloud-provider path (Azure Run Command, etc.).
"""

from enum import Enum

from infrastructure.services.collector_store import CollectorStore


class DataSource(Enum):
    COLLECTOR = "collector"   # fresh in-cluster report available
    PROVIDER = "provider"     # fall back to cloud-provider command path


def get_data_source(cluster_id: str, store: CollectorStore) -> DataSource:
    if store.has_fresh_report(cluster_id):
        return DataSource.COLLECTOR
    return DataSource.PROVIDER
