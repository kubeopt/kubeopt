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
        sensitive_keys = {'client_secret', 'password_hash', 'secret_access_key', 'service_account_json', 'access_key_id', 'api_key', 'jwt_secret'}
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
    # Block writes to internal security settings via the API
    blocked_keys = {'jwt_secret_key', 'flask_secret_key', 'user_password_hash', 'user_username', 'user_role'}
    if body.key.lower() in blocked_keys:
        raise HTTPException(status_code=403, detail=f"Setting '{body.key}' cannot be modified via API")
    try:
        settings_mgr.save_settings({body.key: body.value})

        # If AWS credentials changed, invalidate cached auth so adapters pick up new creds
        if body.key in ('aws_access_key_id', 'aws_secret_access_key', 'aws_region'):
            try:
                from infrastructure.cloud_providers.aws.accounts import AWSAccountManager
                from infrastructure.cloud_providers.aws.executor import AWSKubernetesExecutor
                from infrastructure.cloud_providers.aws.inspector import AWSInfrastructureInspector
                from infrastructure.cloud_providers.aws.metrics import AWSMetricsCollector
                from infrastructure.cloud_providers.aws.costs import AWSCostManager
                AWSAccountManager._auth_instance = None
                AWSKubernetesExecutor._auth_instance = None
                AWSInfrastructureInspector._auth_instance = None
                AWSMetricsCollector._auth_instance = None
                AWSCostManager._auth_instance = None
                logger.info("Invalidated cached AWS authenticators after credential change")
            except Exception:
                pass

        # If GCP credentials changed, write service account key to volume and invalidate cached auth
        if body.key == 'gcp_service_account_key' and body.value:
            import os
            try:
                # Save to volume so it survives container restarts
                volume_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '/app')
                key_path = os.path.join(volume_dir, '.gcp_service_account.json')
                with open(key_path, 'w') as f:
                    f.write(body.value if isinstance(body.value, str) else str(body.value))
                os.chmod(key_path, 0o600)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path
                logger.info(f"GCP service account key saved to {key_path}")
            except Exception as e:
                logger.error(f"Failed to save GCP service account key: {e}")

        # GCP billing settings — propagate to env vars so GCPCostManager can read them
        key_lower = body.key.lower()
        if key_lower == 'gcp_billing_dataset' and body.value:
            import os
            os.environ['GCP_BILLING_DATASET'] = str(body.value)
            logger.info(f"Set GCP_BILLING_DATASET={body.value}")
        if key_lower == 'gcp_billing_account_id' and body.value:
            import os
            os.environ['GCP_BILLING_ACCOUNT_ID'] = str(body.value)
            logger.info(f"Set GCP_BILLING_ACCOUNT_ID={body.value}")

        if body.key in ('gcp_service_account_key', 'gcp_project_id'):
            import os
            if body.key == 'gcp_project_id' and body.value:
                os.environ['GOOGLE_CLOUD_PROJECT'] = str(body.value)
            try:
                from infrastructure.cloud_providers.gcp.accounts import GCPAccountManager
                from infrastructure.cloud_providers.gcp.executor import GCPKubernetesExecutor
                from infrastructure.cloud_providers.gcp.inspector import GCPInfrastructureInspector
                from infrastructure.cloud_providers.gcp.metrics import GCPMetricsCollector
                from infrastructure.cloud_providers.gcp.costs import GCPCostManager
                GCPAccountManager._auth_instance = None
                GCPKubernetesExecutor._auth_instance = None
                GCPInfrastructureInspector._auth_instance = None
                GCPMetricsCollector._auth_instance = None
                GCPCostManager._auth_instance = None
                logger.info("Invalidated cached GCP authenticators after credential change")
            except Exception:
                pass

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
    """Test AWS connection with provided or saved credentials."""
    import os
    try:
        # If creds provided in request, temporarily set them for this test
        if body.access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = body.access_key_id
        if body.secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = body.secret_access_key
        if body.region:
            os.environ['AWS_DEFAULT_REGION'] = body.region
            os.environ['AWS_REGION'] = body.region

        from infrastructure.cloud_providers.aws.authenticator import AWSAuthenticator
        auth = AWSAuthenticator()
        connected = auth.authenticate()  # Force fresh auth attempt
        if connected:
            return {
                "connected": True,
                "message": f"AWS connection successful — Account: {auth.account_id}, Region: {auth.region}",
            }
        else:
            return {"connected": False, "message": "AWS authentication failed — check Access Key ID and Secret Access Key"}
    except Exception as e:
        error_msg = str(e)
        # Sanitize — don't leak credentials in error messages
        for secret_var in ('AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID'):
            if secret_var in os.environ:
                error_msg = error_msg.replace(os.environ[secret_var], '***')
        return {"connected": False, "message": f"AWS connection test failed: {error_msg}"}


@router.post("/test-gcp")
async def test_gcp_connection(
    body: GCPSettings = GCPSettings(),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Test GCP connection with provided or saved credentials."""
    import json as json_mod
    try:
        sa_json = body.service_account_json

        # If no credentials in request body, check saved settings
        if not sa_json:
            try:
                import os
                volume_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '/app')
                key_path = os.path.join(volume_dir, '.gcp_service_account.json')
                if os.path.exists(key_path):
                    with open(key_path, 'r') as f:
                        sa_json = f.read()
            except Exception:
                pass

        if sa_json:
            # Direct credential creation from service account JSON — no ADC, no gcloud needed
            from google.oauth2 import service_account as sa_module
            sa_info = json_mod.loads(sa_json)
            credentials = sa_module.Credentials.from_service_account_info(
                sa_info, scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            project = sa_info.get('project_id') or body.project_id

            # Validate by making an API call
            from google.cloud import container_v1
            client = container_v1.ClusterManagerClient(credentials=credentials)
            # Simple validation: list clusters (even if empty, proves auth works)
            parent = f"projects/{project}/locations/-"
            response = client.list_clusters(parent=parent)
            cluster_count = len(response.clusters)

            return {
                "connected": True,
                "message": f"GCP connected (project: {project}, {cluster_count} cluster(s) found)",
            }
        else:
            # Fall back to ADC (gcloud auth application-default login)
            from infrastructure.cloud_providers.gcp.authenticator import GCPAuthenticator
            auth = GCPAuthenticator()
            connected = auth.authenticate()
            if connected:
                project = auth.project_id or 'unknown'
                return {"connected": True, "message": f"GCP connected via ADC (project: {project})"}
            return {"connected": False, "message": "No GCP credentials. Upload a service account key JSON file."}

    except Exception as e:
        error_msg = str(e)
        # Don't leak private key details
        if 'private_key' in error_msg.lower():
            error_msg = "Invalid service account key format"
        return {"connected": False, "message": f"GCP connection test failed: {error_msg}"}


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
