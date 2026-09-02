"""
CollectorReport schema -- summary pushed by the in-cluster KubeOpt collector.

The collector is a read-only pod running inside the customer's cluster.
It reads the Kubernetes API and metrics-server, then POSTs a summary here.
KubeOpt analysis engine prefers fresh collector data over cloud-provider
command tunnels (e.g. Azure Run Command).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class NodeSummary(BaseModel):
    name: str
    instance_type: str = ""
    cpu_allocatable_m: int = 0          # millicores
    memory_allocatable_mb: int = 0
    cpu_requested_m: int = 0
    memory_requested_mb: int = 0
    cpu_used_m: Optional[int] = None    # live from metrics-server; None if unavailable
    memory_used_mb: Optional[int] = None
    node_pool: str = ""
    zone: str = ""
    ready: bool = True


class PodSummary(BaseModel):
    name: str
    namespace: str
    workload: str = ""          # owning deployment/statefulset/daemonset
    workload_kind: str = ""
    cpu_request_m: int = 0
    memory_request_mb: int = 0
    cpu_limit_m: int = 0
    memory_limit_mb: int = 0
    cpu_used_m: Optional[int] = None
    memory_used_mb: Optional[int] = None
    node: str = ""
    phase: str = "Running"
    restarts: int = 0
    gpu_request: int = 0        # number of GPUs requested (any vendor)
    gpu_limit: int = 0
    gpu_vendor: Optional[str] = None   # e.g. "nvidia.com/gpu", "amd.com/gpu"


class HPASummary(BaseModel):
    name: str
    namespace: str
    target_kind: str
    target_name: str
    min_replicas: int
    max_replicas: int
    current_replicas: int
    desired_replicas: int
    cpu_target_percent: Optional[int] = None


class PVCSummary(BaseModel):
    name: str
    namespace: str
    storage_class: str = ""
    capacity_gb: float = 0.0
    phase: str = "Bound"
    access_modes: list[str] = []


class ServiceSummary(BaseModel):
    name: str
    namespace: str
    type: str                   # ClusterIP, NodePort, LoadBalancer
    load_balancer_ip: str = ""
    ports: list[int] = []


class NamespaceSummary(BaseModel):
    name: str
    pod_count: int = 0
    cpu_requested_m: int = 0
    memory_requested_mb: int = 0
    cpu_used_m: Optional[int] = None
    memory_used_mb: Optional[int] = None
    hpa_count: int = 0
    workload_count: int = 0


class CollectorReport(BaseModel):
    cluster_id: str
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    collector_version: str = "1.0.0"

    nodes: list[NodeSummary] = []
    pods: list[PodSummary] = []
    hpas: list[HPASummary] = []
    pvcs: list[PVCSummary] = []
    services: list[ServiceSummary] = []
    namespaces: list[NamespaceSummary] = []

    # Cluster-level aggregates (pre-computed by collector)
    total_nodes: int = 0
    total_pods: int = 0
    total_cpu_allocatable_m: int = 0
    total_memory_allocatable_mb: int = 0
    total_cpu_requested_m: int = 0
    total_memory_requested_mb: int = 0
    metrics_server_available: bool = False
    metrics_server_error: Optional[str] = None

    # GPU summary (0 when no GPU workloads present)
    total_gpu_pods: int = 0
    total_gpu_requested: int = 0

    def is_fresh(self, max_age_seconds: int = 600) -> bool:
        collected_at = self.collected_at
        if collected_at.tzinfo is None:
            collected_at = collected_at.replace(tzinfo=timezone.utc)
        now = datetime.now(collected_at.tzinfo)
        age = (now - collected_at).total_seconds()
        return age <= max_age_seconds
