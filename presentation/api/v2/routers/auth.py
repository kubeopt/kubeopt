"""Authentication endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from presentation.api.v2.schemas.auth import (
    LoginRequest, LoginResponse, APIKeyRequest, APIKeyResponse, APIKeyValidation,
    LicenseValidateRequest,
)
from presentation.api.v2.dependencies.auth import get_current_user, create_jwt_token
from presentation.api.v2.dependencies.services import (
    get_auth_manager, get_api_security, get_license_validator_dep,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, auth_mgr=Depends(get_auth_manager)):
    """Authenticate and receive a JWT token."""
    try:
        if not auth_mgr.authenticate_user(body.username, body.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        token = create_jwt_token(body.username)
        return LoginResponse(
            token=token,
            expires_in=86400,
            user={"username": body.username, "role": "admin"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh-token")
async def refresh_token(user: Dict[str, Any] = Depends(get_current_user)):
    """Refresh an existing JWT token."""
    username = user.get('sub', 'unknown')
    role = user.get('role', 'admin')
    new_token = create_jwt_token(username, role)
    return {"token": new_token, "token_type": "bearer", "expires_in": 86400}


@router.post("/generate-api-key", response_model=APIKeyResponse)
async def generate_api_key(
    body: APIKeyRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    security_mgr=Depends(get_api_security),
):
    """Generate a new API key."""
    try:
        if hasattr(security_mgr, 'generate_api_key'):
            key = security_mgr.generate_api_key(body.name, body.expires_days)
            return APIKeyResponse(
                api_key=key['api_key'],
                name=body.name,
                expires_at=key.get('expires_at', ''),
            )
    except Exception as e:
        logger.error(f"API key generation failed: {e}")
    raise HTTPException(status_code=500, detail="Failed to generate API key")


@router.post("/validate-api-key")
async def validate_api_key(body: APIKeyValidation, security_mgr=Depends(get_api_security)):
    """Validate an API key."""
    try:
        if hasattr(security_mgr, 'validate_api_key'):
            result = security_mgr.validate_api_key(body.api_key)
            return {"valid": bool(result), "key_info": result or {}}
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
    return {"valid": False}


@router.get("/license/status")
async def license_status(
    user: Dict[str, Any] = Depends(get_current_user),
    validator=Depends(get_license_validator_dep),
):
    """Get current license status."""
    try:
        if hasattr(validator, 'get_license_status'):
            return validator.get_license_status()
    except Exception as e:
        logger.error(f"License status check failed: {e}")
    return {"valid": False, "tier": "FREE", "features": []}


@router.post("/logout")
async def logout():
    """Logout — client should discard the JWT token."""
    return {"status": "success", "message": "Logged out"}


# --- Legacy license endpoints (public, no auth) ---

legacy_router = APIRouter(tags=["license"])


@legacy_router.get("/api/v1/license/info")
async def get_license_info(validator=Depends(get_license_validator_dep)):
    """Get current license information (public)."""
    try:
        if hasattr(validator, 'get_license_info'):
            return validator.get_license_info()
    except Exception as e:
        logger.error(f"License info failed: {e}")
    return {"valid": False, "tier": "FREE"}


@legacy_router.post("/api/v1/license/validate")
async def validate_license(
    body: LicenseValidateRequest,
    validator=Depends(get_license_validator_dep),
):
    """Validate a license key (public)."""
    import os
    old_key = os.environ.get('KUBEOPT_LICENSE_KEY', '')
    try:
        os.environ['KUBEOPT_LICENSE_KEY'] = body.license_key
        validator.license_key = body.license_key
        valid, info = validator.validate_license()

        if valid:
            return {
                "valid": True,
                "tier": info.get("tier"),
                "features": info.get("features"),
                "expires_at": info.get("expires_at"),
            }
        else:
            return {"valid": False, "error": info.get("error", "Invalid license")}
    except Exception as e:
        logger.error(f"License validation failed: {e}")
        return {"valid": False, "error": str(e)}
    finally:
        if old_key:
            os.environ['KUBEOPT_LICENSE_KEY'] = old_key
        elif 'KUBEOPT_LICENSE_KEY' in os.environ:
            del os.environ['KUBEOPT_LICENSE_KEY']
