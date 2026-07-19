"""Analysis and dashboard schemas."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ChartDataResponse(BaseModel):
    chart_type: str
    labels: List[str] = []
    datasets: List[Dict[str, Any]] = []
    options: Optional[Dict[str, Any]] = None


class DashboardOverview(BaseModel):
    cluster_name: str
    cloud_provider: str = "azure"
    optimization_score: float = 0.0
    total_monthly_cost: float = 0.0
    potential_savings: float = 0.0
    node_count: int = 0
    pod_count: int = 0
    health_score: float = 0.0
    top_recommendations: List[Dict[str, Any]] = []
    cost_trend: Optional[Dict[str, Any]] = None


class CPUOptimizationPlan(BaseModel):
    cluster_id: str
    plan: Dict[str, Any] = {}
    recommendations: List[Dict[str, Any]] = []
    estimated_savings: float = 0.0


class RecommendationSchema(BaseModel):
    id: str
    category: str
    title: str
    resource_ref: str
    namespace: str
    monthly_savings: float
    confidence: float
    risk_level: str
    priority_score: float
    evidence: str
    command: Optional[str] = None
    yaml_patch: Optional[str] = None
    rollback: Optional[str] = None
    requires_ai: bool = False
