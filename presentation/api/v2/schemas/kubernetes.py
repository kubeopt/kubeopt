"""Kubernetes data schemas."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PodsOverview(BaseModel):
    cluster_id: str
    pods: List[Dict[str, Any]] = []
    total_pods: int = 0
    namespaces: List[str] = []


class WorkloadsOverview(BaseModel):
    cluster_id: str
    deployments: List[Dict[str, Any]] = []
    statefulsets: List[Dict[str, Any]] = []
    daemonsets: List[Dict[str, Any]] = []
    total_workloads: int = 0


class ResourcesOverview(BaseModel):
    cluster_id: str
    nodes: List[Dict[str, Any]] = []
    total_cpu_cores: float = 0.0
    total_memory_gb: float = 0.0
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
