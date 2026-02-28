"""
License checking dependency for FastAPI.

Replaces Flask's license_middleware before_request hook.
"""

import logging
from typing import Dict, Any

from fastapi import Depends, HTTPException, status

from presentation.api.v2.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)


async def check_license(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Verify the user has a valid license. Returns license info dict.

    Usage:
        @router.post("/generate-plan")
        async def endpoint(license_info: dict = Depends(check_license)):
            ...
    """
    try:
        from presentation.api.v2.services import get_container
        validator = get_container().license_validator
        if hasattr(validator, 'get_license_status'):
            status_info = validator.get_license_status()
            if status_info and status_info.get('valid'):
                return {
                    'tier': status_info.get('tier', 'FREE'),
                    'valid': True,
                    'features': status_info.get('features', []),
                }
    except Exception as e:
        logger.warning(f"License validation error: {e}")

    # Allow free tier by default (same as Flask behavior)
    return {
        'tier': 'FREE',
        'valid': True,
        'features': [],
    }
