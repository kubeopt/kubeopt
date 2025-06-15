#!/usr/bin/env python3
"""
Enterprise API Management & Governance System
Advanced API gateway with rate limiting, versioning, analytics, developer portal,
and comprehensive governance features for enterprise deployment.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import time
from pathlib import Path

# FastAPI and API Gateway
from fastapi import FastAPI, Request, Response, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
import starlette.status as status

# API Documentation
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import yaml

# Rate Limiting & Caching
import redis
import aioredis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Analytics & Monitoring
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Database & Storage
import asyncpg
import motor.motor_asyncio
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Security & Authentication
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import bcrypt

# API Testing & Validation
import jsonschema
from jsonschema import validate, ValidationError
import openapi_spec_validator

# Developer Portal
from jinja2 import Environment, FileSystemLoader

# Utilities
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import ipaddress

logger = structlog.get_logger()

# API Metrics
API_REQUESTS_TOTAL = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status_code', 'api_version'])
API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration', ['method', 'endpoint', 'api_version'])
API_RATE_LIMITS = Counter('api_rate_limits_total', 'API rate limit hits', ['api_key', 'endpoint'])
API_ERRORS = Counter('api_errors_total', 'API errors', ['error_type', 'endpoint'])
ACTIVE_API_KEYS = Gauge('active_api_keys', 'Number of active API keys')

class APIEndpointType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"
    PARTNER = "partner"

class APIVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    BETA = "beta"
    ALPHA = "alpha"

class RateLimitType(str, Enum):
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    REQUESTS_PER_MONTH = "requests_per_month"

class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"

@dataclass
class APIKey:
    """API Key with comprehensive metadata."""
    key_id: str
    api_key: str
    key_hash: str
    name: str
    description: str
    developer_id: str
    organization: str
    status: APIKeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    rate_limits: Dict[RateLimitType, int]
    allowed_endpoints: List[str]
    allowed_ips: List[str]
    scopes: List[str]
    metadata: Dict[str, Any]

@dataclass
class APIEndpoint:
    """API Endpoint configuration."""
    endpoint_id: str
    path: str
    method: str
    version: APIVersion
    endpoint_type: APIEndpointType
    description: str
    rate_limits: Dict[RateLimitType, int]
    authentication_required: bool
    scopes_required: List[str]
    request_schema: Optional[Dict[str, Any]]
    response_schema: Optional[Dict[str, Any]]
    deprecated: bool
    deprecation_date: Optional[datetime]
    replacement_endpoint: Optional[str]
    documentation: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class APIUsageMetrics:
    """API Usage metrics."""
    api_key: str
    endpoint: str
    method: str
    timestamp: datetime
    response_time: float
    status_code: int
    request_size: int
    response_size: int
    ip_address: str
    user_agent: str
    error_message: Optional[str]

@dataclass
class DeveloperAccount:
    """Developer account for API access."""
    developer_id: str
    email: str
    name: str
    organization: str
    tier: str
    status: str
    created_at: datetime
    last_login: Optional[datetime]
    api_keys: List[str]
    usage_quota: Dict[str, int]
    billing_info: Dict[str, Any]
    preferences: Dict[str, Any]

class AdvancedRateLimiter:
    """Advanced rate limiting with multiple strategies."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.algorithms = {
            'sliding_window': self._sliding_window_limit,
            'token_bucket': self._token_bucket_limit,
            'fixed_window': self._fixed_window_limit,
            'adaptive': self._adaptive_limit
        }
    
    async def check_rate_limit(self, key: str, limit: int, window: int, 
                             algorithm: str = 'sliding_window') -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using specified algorithm."""
        try:
            if algorithm not in self.algorithms:
                algorithm = 'sliding_window'
            
            return await self.algorithms[algorithm](key, limit, window)
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, {}  # Fail open
    
    async def _sliding_window_limit(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting."""
        try:
            now = time.time()
            pipeline = self.redis.pipeline()
            
            # Remove old entries
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(uuid.uuid4()): now})
            
            # Set expiration
            pipeline.expire(key, window)
            
            results = await pipeline.execute()
            current_count = results[1]
            
            allowed = current_count < limit
            
            return allowed, {
                'current_count': current_count,
                'limit': limit,
                'window': window,
                'reset_time': now + window,
                'remaining': max(0, limit - current_count - 1)
            }
            
        except Exception as e:
            logger.error(f"Sliding window rate limit failed: {e}")
            return True, {}
    
    async def _token_bucket_limit(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting."""
        try:
            now = time.time()
            bucket_key = f"bucket:{key}"
            
            # Get current bucket state
            bucket_data = await self.redis.hmget(bucket_key, 'tokens', 'last_refill')
            
            tokens = int(bucket_data[0] or limit)
            last_refill = float(bucket_data[1] or now)
            
            # Calculate tokens to add
            time_passed = now - last_refill
            tokens_to_add = int(time_passed * (limit / window))
            tokens = min(limit, tokens + tokens_to_add)
            
            allowed = tokens > 0
            
            if allowed:
                tokens -= 1
            
            # Update bucket
            await self.redis.hmset(bucket_key, {
                'tokens': tokens,
                'last_refill': now
            })
            await self.redis.expire(bucket_key, window * 2)
            
            return allowed, {
                'tokens_remaining': tokens,
                'bucket_size': limit,
                'refill_rate': limit / window,
                'last_refill': now
            }
            
        except Exception as e:
            logger.error(f"Token bucket rate limit failed: {e}")
            return True, {}
    
    async def _fixed_window_limit(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting."""
        try:
            now = time.time()
            window_start = int(now // window) * window
            window_key = f"{key}:{window_start}"
            
            current_count = await self.redis.get(window_key)
            current_count = int(current_count or 0)
            
            allowed = current_count < limit
            
            if allowed:
                pipeline = self.redis.pipeline()
                pipeline.incr(window_key)
                pipeline.expire(window_key, window)
                await pipeline.execute()
                current_count += 1
            
            return allowed, {
                'current_count': current_count,
                'limit': limit,
                'window_start': window_start,
                'window_end': window_start + window,
                'remaining': max(0, limit - current_count)
            }
            
        except Exception as e:
            logger.error(f"Fixed window rate limit failed: {e}")
            return True, {}
    
    async def _adaptive_limit(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Adaptive rate limiting based on system load."""
        try:
            # Get system metrics
            system_load = await self._get_system_load()
            
            # Adjust limit based on load
            if system_load > 0.8:
                adjusted_limit = int(limit * 0.5)  # Reduce by 50%
            elif system_load > 0.6:
                adjusted_limit = int(limit * 0.75)  # Reduce by 25%
            else:
                adjusted_limit = limit
            
            # Use sliding window with adjusted limit
            return await self._sliding_window_limit(key, adjusted_limit, window)
            
        except Exception as e:
            logger.error(f"Adaptive rate limit failed: {e}")
            return True, {}
    
    async def _get_system_load(self) -> float:
        """Get current system load (simplified)."""
        try:
            # In production, this would check actual system metrics
            # CPU usage, memory usage, queue lengths, etc.
            return 0.3  # Placeholder
        except Exception:
            return 0.5  # Default moderate load

class APIKeyManager:
    """Comprehensive API key management."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.api_keys: Dict[str, APIKey] = {}
        self.developers: Dict[str, DeveloperAccount] = {}
        
    async def initialize(self):
        """Initialize API key manager."""
        await self._load_api_keys()
        await self._load_developers()
        
    async def create_api_key(self, developer_id: str, name: str, 
                           scopes: List[str], rate_limits: Dict[RateLimitType, int],
                           expires_in_days: Optional[int] = None) -> APIKey:
        """Create new API key."""
        try:
            # Generate API key
            api_key = self._generate_api_key()
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create API key object
            api_key_obj = APIKey(
                key_id=str(uuid.uuid4()),
                api_key=api_key,
                key_hash=key_hash,
                name=name,
                description=f"API key for {name}",
                developer_id=developer_id,
                organization=self.developers.get(developer_id, {}).get('organization', 'Unknown'),
                status=APIKeyStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                last_used=None,
                usage_count=0,
                rate_limits=rate_limits,
                allowed_endpoints=[],  # All endpoints by default
                allowed_ips=[],  # All IPs by default
                scopes=scopes,
                metadata={}
            )
            
            # Store API key
            self.api_keys[api_key_obj.key_id] = api_key_obj
            
            # Update developer's API keys
            if developer_id in self.developers:
                self.developers[developer_id].api_keys.append(api_key_obj.key_id)
            
            # Save to database
            await self._save_api_key(api_key_obj)
            
            # Update metrics
            ACTIVE_API_KEYS.inc()
            
            logger.info(f"Created API key {api_key_obj.key_id} for developer {developer_id}")
            
            return api_key_obj
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise
    
    async def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate API key and return key object."""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find API key by hash
            for key_obj in self.api_keys.values():
                if key_obj.key_hash == key_hash:
                    # Check status
                    if key_obj.status != APIKeyStatus.ACTIVE:
                        return None
                    
                    # Check expiration
                    if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
                        key_obj.status = APIKeyStatus.EXPIRED
                        await self._save_api_key(key_obj)
                        return None
                    
                    # Update usage
                    key_obj.last_used = datetime.utcnow()
                    key_obj.usage_count += 1
                    await self._save_api_key(key_obj)
                    
                    return key_obj
            
            return None
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        try:
            if key_id in self.api_keys:
                self.api_keys[key_id].status = APIKeyStatus.REVOKED
                await self._save_api_key(self.api_keys[key_id])
                ACTIVE_API_KEYS.dec()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False
    
    def _generate_api_key(self) -> str:
        """Generate secure API key."""
        import secrets
        return f"aks_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(40))}"
    
    async def _load_api_keys(self):
        """Load API keys from database."""
        # Implementation would load from actual database
        pass
    
    async def _load_developers(self):
        """Load developer accounts from database."""
        # Implementation would load from actual database
        pass
    
    async def _save_api_key(self, api_key: APIKey):
        """Save API key to database."""
        # Implementation would save to actual database
        pass

class APIVersionManager:
    """API version management and routing."""
    
    def __init__(self):
        self.versions: Dict[APIVersion, Dict[str, Any]] = {}
        self.routing_rules = {}
        
    def register_version(self, version: APIVersion, config: Dict[str, Any]):
        """Register API version with configuration."""
        self.versions[version] = {
            'config': config,
            'endpoints': {},
            'deprecated': config.get('deprecated', False),
            'deprecation_date': config.get('deprecation_date'),
            'sunset_date': config.get('sunset_date'),
            'documentation_url': config.get('documentation_url'),
            'changelog': config.get('changelog', [])
        }
        
        logger.info(f"Registered API version {version.value}")
    
    def add_endpoint(self, version: APIVersion, endpoint: APIEndpoint):
        """Add endpoint to specific version."""
        if version not in self.versions:
            raise ValueError(f"Version {version.value} not registered")
        
        self.versions[version]['endpoints'][f"{endpoint.method}:{endpoint.path}"] = endpoint
        
    def get_endpoint(self, version: APIVersion, method: str, path: str) -> Optional[APIEndpoint]:
        """Get endpoint for specific version."""
        if version not in self.versions:
            return None
        
        return self.versions[version]['endpoints'].get(f"{method}:{path}")
    
    def check_deprecation(self, version: APIVersion) -> Dict[str, Any]:
        """Check deprecation status of version."""
        if version not in self.versions:
            return {'deprecated': False}
        
        version_info = self.versions[version]
        
        return {
            'deprecated': version_info.get('deprecated', False),
            'deprecation_date': version_info.get('deprecation_date'),
            'sunset_date': version_info.get('sunset_date'),
            'replacement_version': version_info.get('replacement_version'),
            'migration_guide': version_info.get('migration_guide')
        }

class APIAnalytics:
    """Comprehensive API analytics and reporting."""
    
    def __init__(self, storage_backend: str = 'redis'):
        self.storage_backend = storage_backend
        self.metrics_buffer = []
        self.redis_client = None
        
    async def initialize(self):
        """Initialize analytics system."""
        if self.storage_backend == 'redis':
            self.redis_client = aioredis.from_url("redis://localhost:6379")
    
    async def record_request(self, metrics: APIUsageMetrics):
        """Record API request metrics."""
        try:
            # Add to buffer
            self.metrics_buffer.append(metrics)
            
            # Update real-time metrics
            API_REQUESTS_TOTAL.labels(
                method=metrics.method,
                endpoint=metrics.endpoint,
                status_code=metrics.status_code,
                api_version="unknown"  # Would be extracted from request
            ).inc()
            
            API_REQUEST_DURATION.labels(
                method=metrics.method,
                endpoint=metrics.endpoint,
                api_version="unknown"
            ).observe(metrics.response_time)
            
            # Store in Redis for real-time analytics
            if self.redis_client:
                await self._store_metrics_redis(metrics)
            
            # Flush buffer if it's getting large
            if len(self.metrics_buffer) > 1000:
                await self._flush_metrics_buffer()
                
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
    
    async def _store_metrics_redis(self, metrics: APIUsageMetrics):
        """Store metrics in Redis for real-time queries."""
        try:
            timestamp = int(metrics.timestamp.timestamp())
            
            # Store by API key
            key = f"api_metrics:{metrics.api_key}:{timestamp // 3600}"  # Hourly buckets
            await self.redis_client.zadd(key, {json.dumps(asdict(metrics)): timestamp})
            await self.redis_client.expire(key, 86400 * 7)  # Keep for 7 days
            
            # Store by endpoint
            endpoint_key = f"endpoint_metrics:{metrics.endpoint}:{timestamp // 3600}"
            await self.redis_client.zadd(endpoint_key, {json.dumps(asdict(metrics)): timestamp})
            await self.redis_client.expire(endpoint_key, 86400 * 7)
            
        except Exception as e:
            logger.error(f"Failed to store metrics in Redis: {e}")
    
    async def get_usage_report(self, api_key: str, start_date: datetime, 
                             end_date: datetime) -> Dict[str, Any]:
        """Generate usage report for API key."""
        try:
            # Filter metrics for the API key and date range
            filtered_metrics = [
                m for m in self.metrics_buffer
                if m.api_key == api_key and start_date <= m.timestamp <= end_date
            ]
            
            if not filtered_metrics:
                return {
                    'api_key': api_key,
                    'period': f"{start_date.isoformat()} to {end_date.isoformat()}",
                    'total_requests': 0,
                    'endpoints': {},
                    'status_codes': {},
                    'average_response_time': 0,
                    'total_data_transferred': 0
                }
            
            # Calculate statistics
            total_requests = len(filtered_metrics)
            
            endpoints = {}
            status_codes = {}
            response_times = []
            total_request_size = 0
            total_response_size = 0
            
            for metric in filtered_metrics:
                # Endpoint statistics
                if metric.endpoint not in endpoints:
                    endpoints[metric.endpoint] = {
                        'count': 0,
                        'avg_response_time': 0,
                        'status_codes': {}
                    }
                
                endpoints[metric.endpoint]['count'] += 1
                response_times.append(metric.response_time)
                
                # Status code statistics
                status_codes[metric.status_code] = status_codes.get(metric.status_code, 0) + 1
                
                # Data transfer
                total_request_size += metric.request_size
                total_response_size += metric.response_size
            
            # Calculate averages
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            for endpoint in endpoints:
                endpoint_times = [
                    m.response_time for m in filtered_metrics 
                    if m.endpoint == endpoint
                ]
                endpoints[endpoint]['avg_response_time'] = sum(endpoint_times) / len(endpoint_times)
            
            return {
                'api_key': api_key,
                'period': f"{start_date.isoformat()} to {end_date.isoformat()}",
                'total_requests': total_requests,
                'endpoints': endpoints,
                'status_codes': status_codes,
                'average_response_time': avg_response_time,
                'total_data_transferred': {
                    'requests': total_request_size,
                    'responses': total_response_size,
                    'total': total_request_size + total_response_size
                },
                'error_rate': status_codes.get(500, 0) / total_requests * 100 if total_requests > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to generate usage report: {e}")
            return {}
    
    async def _flush_metrics_buffer(self):
        """Flush metrics buffer to persistent storage."""
        try:
            # In production, this would write to a database like PostgreSQL or ClickHouse
            logger.info(f"Flushing {len(self.metrics_buffer)} metrics to persistent storage")
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {e}")

class APIGatewayMiddleware(BaseHTTPMiddleware):
    """Advanced API Gateway middleware with comprehensive features."""
    
    def __init__(self, app, api_key_manager: APIKeyManager, rate_limiter: AdvancedRateLimiter,
                 version_manager: APIVersionManager, analytics: APIAnalytics):
        super().__init__(app)
        self.api_key_manager = api_key_manager
        self.rate_limiter = rate_limiter
        self.version_manager = version_manager
        self.analytics = analytics
        
    async def dispatch(self, request: Request, call_next):
        """Process request through API gateway."""
        start_time = time.time()
        api_key_obj = None
        
        try:
            # Extract API version from URL or header
            api_version = self._extract_api_version(request)
            
            # Check if endpoint exists
            endpoint = self.version_manager.get_endpoint(
                api_version, request.method, request.url.path
            )
            
            if not endpoint:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Endpoint not found", "code": "ENDPOINT_NOT_FOUND"}
                )
            
            # Check deprecation
            deprecation_info = self.version_manager.check_deprecation(api_version)
            
            # Authentication
            if endpoint.authentication_required:
                api_key_obj = await self._authenticate_request(request)
                if not api_key_obj:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Invalid API key", "code": "INVALID_API_KEY"}
                    )
                
                # Check scopes
                if endpoint.scopes_required:
                    if not any(scope in api_key_obj.scopes for scope in endpoint.scopes_required):
                        return JSONResponse(
                            status_code=403,
                            content={"error": "Insufficient permissions", "code": "INSUFFICIENT_SCOPES"}
                        )
            
            # Rate limiting
            if api_key_obj:
                rate_limit_key = f"api_key:{api_key_obj.key_id}"
                
                # Check endpoint-specific rate limits
                for limit_type, limit_value in endpoint.rate_limits.items():
                    window = self._get_rate_limit_window(limit_type)
                    allowed, limit_info = await self.rate_limiter.check_rate_limit(
                        f"{rate_limit_key}:{limit_type.value}",
                        limit_value,
                        window
                    )
                    
                    if not allowed:
                        API_RATE_LIMITS.labels(
                            api_key=api_key_obj.key_id,
                            endpoint=request.url.path
                        ).inc()
                        
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "Rate limit exceeded",
                                "code": "RATE_LIMIT_EXCEEDED",
                                "limit_info": limit_info
                            },
                            headers={
                                "X-RateLimit-Limit": str(limit_value),
                                "X-RateLimit-Remaining": str(limit_info.get('remaining', 0)),
                                "X-RateLimit-Reset": str(limit_info.get('reset_time', 0))
                            }
                        )
            
            # IP address validation
            if api_key_obj and api_key_obj.allowed_ips:
                client_ip = self._get_client_ip(request)
                if not self._is_ip_allowed(client_ip, api_key_obj.allowed_ips):
                    return JSONResponse(
                        status_code=403,
                        content={"error": "IP address not allowed", "code": "IP_NOT_ALLOWED"}
                    )
            
            # Request validation
            if endpoint.request_schema:
                if not await self._validate_request(request, endpoint.request_schema):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request format", "code": "INVALID_REQUEST"}
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add headers
            response.headers["X-API-Version"] = api_version.value
            response.headers["X-Request-ID"] = str(uuid.uuid4())
            
            if deprecation_info['deprecated']:
                response.headers["Deprecation"] = "true"
                if deprecation_info['sunset_date']:
                    response.headers["Sunset"] = deprecation_info['sunset_date'].isoformat()
            
            # Record analytics
            await self._record_analytics(request, response, api_key_obj, start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"API Gateway middleware error: {e}")
            
            # Record error analytics
            if api_key_obj:
                await self._record_analytics(request, None, api_key_obj, start_time, error=str(e))
            
            API_ERRORS.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()
            
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "code": "INTERNAL_ERROR"}
            )
    
    def _extract_api_version(self, request: Request) -> APIVersion:
        """Extract API version from request."""
        # Check URL path
        path_parts = request.url.path.split('/')
        if len(path_parts) > 2 and path_parts[1] == 'api':
            version_str = path_parts[2]
            try:
                return APIVersion(version_str)
            except ValueError:
                pass
        
        # Check header
        version_header = request.headers.get('API-Version')
        if version_header:
            try:
                return APIVersion(version_header)
            except ValueError:
                pass
        
        # Default to v2
        return APIVersion.V2
    
    async def _authenticate_request(self, request: Request) -> Optional[APIKey]:
        """Authenticate API request."""
        try:
            # Check for API key in header
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                # Check for Bearer token
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    api_key = auth_header[7:]
            
            if not api_key:
                return None
            
            return await self.api_key_manager.validate_api_key(api_key)
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def _get_rate_limit_window(self, limit_type: RateLimitType) -> int:
        """Get window size in seconds for rate limit type."""
        windows = {
            RateLimitType.REQUESTS_PER_MINUTE: 60,
            RateLimitType.REQUESTS_PER_HOUR: 3600,
            RateLimitType.REQUESTS_PER_DAY: 86400,
            RateLimitType.REQUESTS_PER_MONTH: 2592000
        }
        return windows.get(limit_type, 3600)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    def _is_ip_allowed(self, client_ip: str, allowed_ips: List[str]) -> bool:
        """Check if client IP is in allowed list."""
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for allowed in allowed_ips:
                try:
                    if '/' in allowed:
                        # CIDR notation
                        if client_addr in ipaddress.ip_network(allowed):
                            return True
                    else:
                        # Single IP
                        if client_addr == ipaddress.ip_address(allowed):
                            return True
                except ValueError:
                    continue
            
            return False
            
        except Exception:
            return True  # Allow if validation fails
    
    async def _validate_request(self, request: Request, schema: Dict[str, Any]) -> bool:
        """Validate request against JSON schema."""
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.json()
                    validate(instance=body, schema=schema)
                    return True
                except (json.JSONDecodeError, ValidationError):
                    return False
            
            return True  # No validation needed for GET requests
            
        except Exception:
            return False
    
    async def _record_analytics(self, request: Request, response: Optional[Response],
                               api_key: Optional[APIKey], start_time: float,
                               error: Optional[str] = None):
        """Record request analytics."""
        try:
            end_time = time.time()
            response_time = end_time - start_time
            
            # Get request/response sizes
            request_size = int(request.headers.get('Content-Length', 0))
            response_size = 0
            status_code = 500 if error else (response.status_code if response else 200)
            
            if response and hasattr(response, 'headers'):
                response_size = int(response.headers.get('Content-Length', 0))
            
            metrics = APIUsageMetrics(
                api_key=api_key.key_id if api_key else 'anonymous',
                endpoint=request.url.path,
                method=request.method,
                timestamp=datetime.utcnow(),
                response_time=response_time,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get('User-Agent', ''),
                error_message=error
            )
            
            await self.analytics.record_request(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record analytics: {e}")

class DeveloperPortal:
    """Developer portal for API documentation and key management."""
    
    def __init__(self, api_key_manager: APIKeyManager, analytics: APIAnalytics):
        self.api_key_manager = api_key_manager
        self.analytics = analytics
        self.app = FastAPI(title="Developer Portal")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup developer portal routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def portal_home():
            """Developer portal home page."""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>AKS Intelligence API - Developer Portal</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { background: #667eea; color: white; padding: 20px; border-radius: 8px; }
                    .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                    .endpoint { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 4px; }
                    .method { font-weight: bold; }
                    .get { color: #28a745; }
                    .post { color: #007bff; }
                    .put { color: #ffc107; }
                    .delete { color: #dc3545; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🚀 AKS Intelligence API</h1>
                    <p>Enterprise-grade cost optimization API with AI-powered insights</p>
                </div>
                
                <div class="section">
                    <h2>📖 Quick Start</h2>
                    <ol>
                        <li>Register for a developer account</li>
                        <li>Generate your API key</li>
                        <li>Start making requests to our endpoints</li>
                    </ol>
                </div>
                
                <div class="section">
                    <h2>🔑 Authentication</h2>
                    <p>Include your API key in the request header:</p>
                    <code>X-API-Key: your_api_key_here</code>
                </div>
                
                <div class="section">
                    <h2>📊 API Endpoints</h2>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span> /api/v2/clusters
                        <p>List all monitored AKS clusters</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span> /api/v2/clusters/{cluster_id}/analyze
                        <p>Start cost analysis for specific cluster</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span> /api/v2/recommendations
                        <p>Get AI-powered cost optimization recommendations</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span> /api/v2/insights
                        <p>Get advanced analytics and predictions</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📈 Rate Limits</h2>
                    <ul>
                        <li>Free Tier: 1,000 requests/hour</li>
                        <li>Pro Tier: 10,000 requests/hour</li>
                        <li>Enterprise: Custom limits</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🔗 Resources</h2>
                    <ul>
                        <li><a href="/docs">Interactive API Documentation</a></li>
                        <li><a href="/developer/keys">Manage API Keys</a></li>
                        <li><a href="/developer/analytics">Usage Analytics</a></li>
                        <li><a href="/support">Support & Contact</a></li>
                    </ul>
                </div>
            </body>
            </html>
            """
        
        @self.app.get("/developer/keys")
        async def api_keys_page():
            """API keys management page."""
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>API Keys - Developer Portal</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { background: #667eea; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .form-group { margin: 15px 0; }
                    label { display: block; margin-bottom: 5px; font-weight: bold; }
                    input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                    button { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
                    button:hover { background: #5a6fd8; }
                    .key-card { background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔑 API Key Management</h1>
                        <p>Create and manage your API keys</p>
                    </div>
                    
                    <h2>Create New API Key</h2>
                    <form id="createKeyForm">
                        <div class="form-group">
                            <label for="keyName">Key Name</label>
                            <input type="text" id="keyName" placeholder="My Application Key" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="scopes">Scopes</label>
                            <select id="scopes" multiple>
                                <option value="read:clusters">Read Clusters</option>
                                <option value="write:clusters">Write Clusters</option>
                                <option value="read:costs">Read Costs</option>
                                <option value="read:recommendations">Read Recommendations</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="expiryDays">Expiry (Days)</label>
                            <select id="expiryDays">
                                <option value="">Never</option>
                                <option value="30">30 Days</option>
                                <option value="90">90 Days</option>
                                <option value="365">1 Year</option>
                            </select>
                        </div>
                        
                        <button type="submit">Create API Key</button>
                    </form>
                    
                    <h2>Your API Keys</h2>
                    <div id="apiKeys">
                        <div class="key-card">
                            <h3>Development Key</h3>
                            <p><strong>Key ID:</strong> dev-key-001</p>
                            <p><strong>Created:</strong> 2024-01-15</p>
                            <p><strong>Last Used:</strong> 2024-01-20</p>
                            <p><strong>Requests:</strong> 1,247</p>
                            <p><strong>Status:</strong> Active</p>
                            <button onclick="revokeKey('dev-key-001')">Revoke</button>
                        </div>
                    </div>
                </div>
                
                <script>
                    document.getElementById('createKeyForm').addEventListener('submit', async function(e) {
                        e.preventDefault();
                        
                        const formData = {
                            name: document.getElementById('keyName').value,
                            scopes: Array.from(document.getElementById('scopes').selectedOptions).map(o => o.value),
                            expiry_days: document.getElementById('expiryDays').value || null
                        };
                        
                        try {
                            const response = await fetch('/api/developer/keys', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(formData)
                            });
                            
                            if (response.ok) {
                                const result = await response.json();
                                alert('API Key created: ' + result.api_key);
                                location.reload();
                            } else {
                                alert('Failed to create API key');
                            }
                        } catch (error) {
                            alert('Error: ' + error.message);
                        }
                    });
                    
                    async function revokeKey(keyId) {
                        if (confirm('Are you sure you want to revoke this API key?')) {
                            try {
                                const response = await fetch(`/api/developer/keys/${keyId}`, {
                                    method: 'DELETE'
                                });
                                
                                if (response.ok) {
                                    alert('API key revoked');
                                    location.reload();
                                } else {
                                    alert('Failed to revoke API key');
                                }
                            } catch (error) {
                                alert('Error: ' + error.message);
                            }
                        }
                    }
                </script>
            </body>
            </html>
            """)
        
        @self.app.post("/api/developer/keys")
        async def create_api_key(request: Request):
            """Create new API key."""
            try:
                data = await request.json()
                
                # In production, get developer_id from authentication
                developer_id = "demo-developer"
                
                api_key = await self.api_key_manager.create_api_key(
                    developer_id=developer_id,
                    name=data['name'],
                    scopes=data['scopes'],
                    rate_limits={
                        RateLimitType.REQUESTS_PER_HOUR: 1000,
                        RateLimitType.REQUESTS_PER_DAY: 10000
                    },
                    expires_in_days=data.get('expiry_days')
                )
                
                return {
                    "key_id": api_key.key_id,
                    "api_key": api_key.api_key,  # Only show once
                    "name": api_key.name,
                    "scopes": api_key.scopes,
                    "created_at": api_key.created_at.isoformat()
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

class EnterpriseAPIGateway:
    """Main enterprise API gateway application."""
    
    def __init__(self):
        self.app = FastAPI(
            title="AKS Cost Intelligence API Gateway",
            description="Enterprise-grade API gateway with advanced features",
            version="2.0.0"
        )
        
        # Initialize components
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
        self.rate_limiter = AdvancedRateLimiter(self.redis_client)
        self.api_key_manager = APIKeyManager("postgresql://localhost/api_gateway")
        self.version_manager = APIVersionManager()
        self.analytics = APIAnalytics()
        self.developer_portal = DeveloperPortal(self.api_key_manager, self.analytics)
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        self._register_api_versions()
    
    async def initialize(self):
        """Initialize all components."""
        await self.api_key_manager.initialize()
        await self.analytics.initialize()
        
    def _setup_middleware(self):
        """Setup middleware stack."""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # API Gateway middleware
        gateway_middleware = APIGatewayMiddleware(
            self.app,
            self.api_key_manager,
            self.rate_limiter,
            self.version_manager,
            self.analytics
        )
        self.app.add_middleware(BaseHTTPMiddleware, dispatch=gateway_middleware.dispatch)
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint."""
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
        # Mount developer portal
        self.app.mount("/developer", self.developer_portal.app)
    
    def _register_api_versions(self):
        """Register API versions and endpoints."""
        # Register V2 API
        self.version_manager.register_version(APIVersion.V2, {
            'description': 'Current stable API version',
            'deprecated': False,
            'documentation_url': '/docs/v2'
        })
        
        # Register sample endpoints
        endpoints = [
            APIEndpoint(
                endpoint_id="list_clusters_v2",
                path="/api/v2/clusters",
                method="GET",
                version=APIVersion.V2,
                endpoint_type=APIEndpointType.PUBLIC,
                description="List all monitored AKS clusters",
                rate_limits={
                    RateLimitType.REQUESTS_PER_HOUR: 1000
                },
                authentication_required=True,
                scopes_required=["read:clusters"],
                request_schema=None,
                response_schema={
                    "type": "object",
                    "properties": {
                        "clusters": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                },
                deprecated=False,
                deprecation_date=None,
                replacement_endpoint=None,
                documentation={
                    "summary": "List clusters",
                    "description": "Returns a list of all monitored AKS clusters",
                    "examples": {}
                },
                metadata={}
            )
        ]
        
        for endpoint in endpoints:
            self.version_manager.add_endpoint(endpoint.version, endpoint)

# Example usage
if __name__ == "__main__":
    import uvicorn
    
    async def main():
        # Create and initialize gateway
        gateway = EnterpriseAPIGateway()
        await gateway.initialize()
        
        # Run the server
        config = uvicorn.Config(
            app=gateway.app,
            host="0.0.0.0",
            port=8080,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    asyncio.run(main())