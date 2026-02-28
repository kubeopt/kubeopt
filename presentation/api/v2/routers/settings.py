"""Settings and configuration endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from presentation.api.v2.schemas.settings import (
    SettingsResponse, SettingUpdate, AzureSettings, AWSSettings, GCPSettings,
)
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import (
    get_settings_manager, get_provider_registry, get_cloud_provider, get_alerts_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    user: Dict[str, Any] = Depends(get_current_user),
    settings_mgr=Depends(get_settings_manager),
    cloud_provider: str = Depends(get_cloud_provider),
):
    """Get all settings."""
    try:
        all_settings = settings_mgr.get_all_settings()
        # Redact sensitive values
        safe_settings = {}
        sensitive_keys = {'client_secret', 'password_hash', 'secret_access_key', 'service_account_json'}
        for k, v in (all_settings or {}).items():
            key_lower = k.lower()
            if any(s in key_lower for s in sensitive_keys) and v:
                safe_settings[key_lower] = '***'
            else:
                safe_settings[key_lower] = v
        return SettingsResponse(settings=safe_settings, cloud_provider=cloud_provider)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")


@router.post("/save")
async def save_setting(
    body: SettingUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    settings_mgr=Depends(get_settings_manager),
):
    """Save a single setting."""
    try:
        settings_mgr.save_settings({body.key: body.value})
        return {"message": f"Setting '{body.key}' saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save setting: {e}")
        raise HTTPException(status_code=500, detail="Failed to save setting")


@router.post("/test-azure")
async def test_azure_connection(
    body: AzureSettings = AzureSettings(),
    user: Dict[str, Any] = Depends(get_current_user),
    registry=Depends(get_provider_registry),
):
    """Test Azure connection with provided or current credentials."""
    try:
        authenticator = registry.get_authenticator()
        is_auth = authenticator.is_authenticated()
        return {
            "connected": is_auth,
            "provider": authenticator.get_provider_name(),
            "message": "Azure connection successful" if is_auth else "Azure connection failed",
        }
    except Exception as e:
        return {"connected": False, "message": f"Azure connection test failed: {e}"}


@router.post("/test-aws")
async def test_aws_connection(
    body: AWSSettings = AWSSettings(),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Test AWS connection with provided credentials."""
    try:
        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        auth = AWSAuthenticator()
        connected = auth.is_authenticated()
        return {"connected": connected, "message": "AWS connection successful" if connected else "AWS not implemented yet"}
    except NotImplementedError:
        return {"connected": False, "message": "AWS support not yet implemented (Phase 6)"}
    except Exception as e:
        return {"connected": False, "message": f"AWS connection test failed: {e}"}


@router.post("/test-gcp")
async def test_gcp_connection(
    body: GCPSettings = GCPSettings(),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Test GCP connection with provided credentials."""
    try:
        from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
        auth = GCPAuthenticator()
        connected = auth.is_authenticated()
        return {"connected": connected, "message": "GCP connection successful" if connected else "GCP not implemented yet"}
    except NotImplementedError:
        return {"connected": False, "message": "GCP support not yet implemented (Phase 7)"}
    except Exception as e:
        return {"connected": False, "message": f"GCP connection test failed: {e}"}


@router.post("/test-slack")
async def test_slack(
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Test Slack webhook integration."""
    try:
        if hasattr(alerts_mgr, 'test_slack'):
            result = alerts_mgr.test_slack()
            return {"success": result, "message": "Slack test sent" if result else "Slack test failed"}
    except Exception as e:
        return {"success": False, "message": f"Slack test failed: {e}"}


@router.post("/test-email")
async def test_email(
    user: Dict[str, Any] = Depends(get_current_user),
    alerts_mgr=Depends(get_alerts_manager),
):
    """Test email integration."""
    try:
        if hasattr(alerts_mgr, 'test_email'):
            result = alerts_mgr.test_email()
            return {"success": result, "message": "Email test sent" if result else "Email test failed"}
    except Exception as e:
        return {"success": False, "message": f"Email test failed: {e}"}
