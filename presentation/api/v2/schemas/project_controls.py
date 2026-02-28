"""Project controls schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):
    deployment_frequency_target: float
    change_failure_tolerance: float
    capacity_buffer_target: float
    compliance_minimum: float
    utilization_target: float


class EnvironmentsUpdateRequest(BaseModel):
    environments: Dict[str, EnvironmentConfig]
    default_environment: str = "development"
