from enum import Enum
from typing import Optional
from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationCategory(str, Enum):
    RIGHTSIZING = "rightsizing"
    IDLE_WORKLOAD = "idle_workload"
    HPA = "hpa"
    NODE_POOL = "node_pool"
    STORAGE = "storage"


class Recommendation(BaseModel):
    id: str
    category: RecommendationCategory
    title: str
    resource_ref: str
    namespace: str
    monthly_savings: float
    confidence: float  # 0.0-1.0
    risk_level: RiskLevel
    priority_score: float  # monthly_savings * confidence * risk_weight
    evidence: str
    command: Optional[str] = None
    yaml_patch: Optional[str] = None
    rollback: Optional[str] = None
    requires_ai: bool = False

    model_config = {"use_enum_values": True}
