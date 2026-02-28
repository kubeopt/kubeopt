"""Subscription/account management endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from presentation.api.v2.schemas.subscriptions import SubscriptionInfo, SubscriptionListResponse
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_account_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    user: Dict[str, Any] = Depends(get_current_user),
    account_mgr=Depends(get_account_manager),
):
    """List available cloud subscriptions/accounts."""
    try:
        accounts = account_mgr.list_accounts()
        items = [
            SubscriptionInfo(
                subscription_id=a.get('id', ''),
                subscription_name=a.get('name', ''),
                tenant_id=a.get('tenant_id', ''),
                state=a.get('state', ''),
                is_default=a.get('is_default', False),
            )
            for a in (accounts or [])
        ]
        return SubscriptionListResponse(subscriptions=items, total=len(items))
    except Exception as e:
        logger.error(f"Failed to list subscriptions: {e}")
        return SubscriptionListResponse(subscriptions=[], total=0)


@router.get("/dropdown")
async def subscriptions_dropdown(
    user: Dict[str, Any] = Depends(get_current_user),
    account_mgr=Depends(get_account_manager),
):
    """Get subscriptions formatted for dropdown selector."""
    try:
        accounts = account_mgr.list_accounts()
        return {
            "subscriptions": [
                {
                    "id": a.get('id', ''),
                    "name": a.get('name', ''),
                    "is_default": a.get('is_default', False),
                }
                for a in (accounts or [])
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get subscription dropdown: {e}")
        return {"subscriptions": []}


@router.post("/{subscription_id}/validate")
async def validate_subscription(
    subscription_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    account_mgr=Depends(get_account_manager),
):
    """Validate access to a subscription and its clusters."""
    try:
        from infrastructure.cloud_providers.types import ClusterIdentifier, CloudProvider
        cluster_id = ClusterIdentifier(
            provider=CloudProvider.AZURE,
            subscription_id=subscription_id,
            cluster_name="",
            region="",
        )
        result = account_mgr.validate_cluster_access(cluster_id)
        return {"accessible": bool(result)}
    except Exception as e:
        logger.error(f"Failed to validate subscription {subscription_id}: {e}")
        return {"accessible": False, "error": str(e)}
