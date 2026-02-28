"""
Rate limiting dependency for FastAPI.

Replaces Flask's @api_security.rate_limit decorator.
Simple in-memory sliding window rate limiter.
"""

import time
import logging
from collections import defaultdict
from typing import Callable

from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# In-memory store: {key: [timestamps]}
_request_log: dict = defaultdict(list)


def rate_limit(max_requests: int = 60, window_seconds: int = 60) -> Callable:
    """
    Create a rate limit dependency.

    Usage:
        @router.get("/endpoint", dependencies=[Depends(rate_limit(max=10, window=60))])
        async def endpoint():
            ...
    """
    async def _check_rate_limit(request: Request):
        # Key by client IP
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"

        now = time.time()
        cutoff = now - window_seconds

        # Clean old entries and check count
        timestamps = _request_log[key]
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s.",
            )

        timestamps.append(now)

    return _check_rate_limit
