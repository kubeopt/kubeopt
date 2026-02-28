"""Plan generation schemas."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PlanGenerateRequest(BaseModel):
    strategy: str = "balanced"
    force_regenerate: bool = False


class PlanResponse(BaseModel):
    plan_id: str
    cluster_id: str
    strategy: str
    status: str = "completed"
    created_at: Optional[str] = None
    plan_data: Optional[Dict[str, Any]] = None
    total_savings: float = 0.0
    total_commands: int = 0


class ImplementationPlan(BaseModel):
    plan_id: str
    phases: List[Dict[str, Any]] = []
    total_estimated_hours: float = 0.0
    total_savings: float = 0.0
    success_probability: float = 0.0
