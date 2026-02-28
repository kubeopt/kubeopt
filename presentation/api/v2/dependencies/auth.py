"""
Authentication dependency for FastAPI.

Replaces Flask's @auth_manager.require_auth decorator and hybrid_auth.
Supports JWT Bearer tokens and API keys.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv('JWT_SECRET_KEY', os.getenv('FLASK_SECRET_KEY', 'kubeopt-dev-secret'))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def _decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        exp = payload.get('exp')
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
        return payload
    except Exception:
        return None


def create_jwt_token(username: str, role: str = "admin") -> str:
    """Create a new JWT token."""
    from jose import jwt
    payload = {
        'sub': username,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate an API key against stored keys."""
    try:
        from presentation.api.v2.services import get_container
        security_mgr = get_container().api_security
        if hasattr(security_mgr, 'validate_api_key'):
            result = security_mgr.validate_api_key(api_key)
            if result:
                return {'sub': 'api_key_user', 'role': 'api', 'api_key': True}
    except Exception as e:
        logger.debug(f"API key validation failed: {e}")
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency: authenticate via JWT Bearer token, API key, or query param ?token=.

    The query param fallback is needed for SSE (EventSource) which can't set headers.

    Usage:
        @router.get("/protected")
        async def endpoint(user: dict = Depends(get_current_user)):
            ...
    """
    raw_token = None

    if credentials is not None:
        raw_token = credentials.credentials
    elif token:
        # Fallback for EventSource / SSE streams
        raw_token = token

    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try JWT first
    payload = _decode_jwt(raw_token)
    if payload:
        return payload

    # Try API key
    api_user = _validate_api_key(raw_token)
    if api_user:
        return api_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Like get_current_user but returns None instead of raising on failure."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
