"""Cluster management schemas."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .common import CloudProviderEnum


class ClusterCreate(BaseModel):
    cluster_name: str = Field(..., min_length=1, max_length=200)
    cloud_provider: CloudProviderEnum = CloudProviderEnum.AZURE

    # Azure-specific
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None

    # AWS-specific
    account_id: Optional[str] = None
    region: Optional[str] = None

    # GCP-specific
    project_id: Optional[str] = None
    zone: Optional[str] = None


class ClusterResponse(BaseModel):
    cluster_id: str
    cluster_name: str
    cloud_provider: str = "azure"
    region: Optional[str] = None
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    last_analysis: Optional[str] = None
    optimization_score: Optional[float] = None
    total_cost: Optional[float] = None
    potential_savings: Optional[float] = None
    node_count: Optional[int] = None
    status: str = "active"


class ClusterListResponse(BaseModel):
    clusters: List[ClusterResponse]
    total: int


class PortfolioSummary(BaseModel):
    total_clusters: int = 0
    total_monthly_cost: float = 0.0
    total_potential_savings: float = 0.0
    total_nodes: int = 0
    average_optimization_score: float = 0.0
    clusters_needing_attention: int = 0


class AnalysisStatus(BaseModel):
    session_key: str
    status: str
    progress: float = 0.0
    current_phase: Optional[str] = None
    message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
