"""Settings schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    settings: Dict[str, Any]
    cloud_provider: str = "azure"


class SettingUpdate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: Any


class AzureSettings(BaseModel):
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    subscription_id: Optional[str] = None


class AWSSettings(BaseModel):
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region: Optional[str] = None
    enable_cost_explorer: bool = True


class GCPSettings(BaseModel):
    project_id: Optional[str] = None
    service_account_json: Optional[str] = None
    zone: Optional[str] = None
    enable_billing_api: bool = True
    billing_dataset: Optional[str] = None
    billing_account_id: Optional[str] = None
