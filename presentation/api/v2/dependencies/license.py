"""
License checking dependency for FastAPI.

Validates access to hosted/commercial features. The open-source core does not
require this dependency.
"""

import logging
from typing import Dict, Any

from fastapi import Depends, HTTPException, status

from presentation.api.v2.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)


async def check_license(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Verify the user has a valid license for hosted/commercial features.
    Raises 403 if no valid license found.

    Usage:
        @router.post("/generate-plan")
        async def endpoint(license_info: dict = Depends(check_license)):
            ...
    """
    try:
        from infrastructure.services.license_validator import get_license_validator, LicenseTier
        validator = get_license_validator()
        tier = validator.get_tier()

        if tier == LicenseTier.NONE:
            raise HTTPException(
                status_code=403,
                detail="This hosted feature requires a valid PRO or ENTERPRISE license"
            )

        return {
            'tier': tier.value.upper(),
            'valid': True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"License validation error: {e}")
        raise HTTPException(
            status_code=503,
            detail="License validation service unavailable"
        )
