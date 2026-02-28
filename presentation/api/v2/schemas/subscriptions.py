"""Subscription/account schemas."""

from typing import Optional, List
from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    subscription_id: str
    subscription_name: str
    tenant_id: Optional[str] = None
    state: str = "Enabled"
    is_default: bool = False


class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionInfo]
    total: int
