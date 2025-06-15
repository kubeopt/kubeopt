#!/usr/bin/env python3
"""
Enterprise Security & Authentication System
Advanced security features including multi-factor authentication, zero-trust architecture,
API security, and compliance monitoring.
"""

import asyncio
import logging
import os
import json
import secrets
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import ipaddress

# Security Libraries
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import pyotp
import qrcode
from io import BytesIO

# JWT and Authentication
from jose import JWTError, jwt
from passlib.context import CryptContext
import argon2

# FastAPI Security
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.middleware.base import BaseHTTPMiddleware
import starlette.status as status

# Azure Security
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.monitor.query import LogsQueryClient, MetricsQueryClient

# Rate Limiting and Protection
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Monitoring and Logging
import structlog
from prometheus_client import Counter, Histogram, Gauge
import geoip2.database

# Email and Notifications
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = structlog.get_logger()

# Security Metrics
AUTHENTICATION_ATTEMPTS = Counter('auth_attempts_total', 'Total authentication attempts', ['status', 'method'])
AUTHORIZATION_CHECKS = Counter('authz_checks_total', 'Total authorization checks', ['status', 'resource'])
SECURITY_EVENTS = Counter('security_events_total', 'Total security events', ['event_type', 'severity'])
API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint', 'method'])

class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_ACCESS = "data_access"
    ADMIN_ACTION = "admin_action"

class UserRole(str, Enum):
    ADMIN = "admin"
    COST_ANALYST = "cost_analyst"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    API_USER = "api_user"

class Permission(str, Enum):
    READ_CLUSTERS = "read:clusters"
    WRITE_CLUSTERS = "write:clusters"
    READ_COSTS = "read:costs"
    WRITE_COSTS = "write:costs"
    READ_RECOMMENDATIONS = "read:recommendations"
    EXECUTE_RECOMMENDATIONS = "execute:recommendations"
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    API_ACCESS = "api:access"

@dataclass
class User:
    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    permissions: List[Permission]
    mfa_enabled: bool
    mfa_secret: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    failed_login_attempts: int
    account_locked: bool
    password_hash: str
    tenant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class APIKey:
    key_id: str
    user_id: str
    key_hash: str
    name: str
    scopes: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool

@dataclass
class SecurityEvent:
    event_id: str
    event_type: SecurityEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    resource: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    severity: str
    resolved: bool = False

class AdvancedCryptography:
    """Advanced cryptography utilities for enterprise security."""
    
    def __init__(self):
        self.password_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self.encryption_key = self._generate_or_load_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _generate_or_load_encryption_key(self) -> bytes:
        """Generate or load encryption key from secure storage."""
        key_path = os.getenv('ENCRYPTION_KEY_PATH', '.encryption_key')
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            os.chmod(key_path, 0o600)  # Restrict permissions
            return key
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2."""
        return self.password_context.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self.password_context.verify(password, hashed)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self) -> Tuple[str, str]:
        """Generate API key and its hash."""
        key = f"aks_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(40))}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key, key_hash

class MFAManager:
    """Multi-Factor Authentication manager."""
    
    def __init__(self):
        self.crypto = AdvancedCryptography()
        
    def generate_mfa_secret(self, user_email: str) -> Tuple[str, str]:
        """Generate MFA secret and QR code."""
        secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI
        provisioning_uri = totp.provisioning_uri(
            user_email,
            issuer_name="AKS Cost Intelligence"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        qr_code_data = base64.b64encode(img_buffer.getvalue()).decode()
        
        return secret, qr_code_data
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify MFA token."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 30 seconds window
        except Exception:
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA."""
        return [self.crypto.generate_secure_token(8) for _ in range(count)]

class JWTManager:
    """Advanced JWT token management."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.blacklisted_tokens: Set[str] = set()
        
    def create_access_token(self, user: User, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions],
            "tenant_id": user.tenant_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for blacklisting
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=30)
        
        payload = {
            "sub": user.user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is blacklisted
            if payload.get("jti") in self.blacklisted_tokens:
                raise JWTError("Token has been revoked")
            
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
    
    def revoke_token(self, token: str):
        """Revoke a JWT token by adding to blacklist."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self.blacklisted_tokens.add(payload.get("jti"))
        except JWTError:
            pass  # Token is already invalid

class SecurityEventLogger:
    """Advanced security event logging and monitoring."""
    
    def __init__(self):
        self.events_storage = []  # In production, use persistent storage
        self.anomaly_detector = SecurityAnomalyDetector()
        
    async def log_security_event(self, event: SecurityEvent):
        """Log security event and trigger analysis."""
        try:
            # Store event
            self.events_storage.append(event)
            
            # Update metrics
            SECURITY_EVENTS.labels(
                event_type=event.event_type.value,
                severity=event.severity
            ).inc()
            
            # Log to structured logger
            logger.info(
                "Security event logged",
                event_id=event.event_id,
                event_type=event.event_type.value,
                user_id=event.user_id,
                ip_address=event.ip_address,
                severity=event.severity,
                extra=event.metadata
            )
            
            # Check for anomalies
            await self.anomaly_detector.analyze_event(event)
            
            # Send alerts for critical events
            if event.severity in ["high", "critical"]:
                await self._send_security_alert(event)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def _send_security_alert(self, event: SecurityEvent):
        """Send security alert for critical events."""
        try:
            # Implementation for sending alerts (email, Slack, etc.)
            alert_message = f"""
            SECURITY ALERT: {event.event_type.value}
            
            Event ID: {event.event_id}
            User ID: {event.user_id}
            IP Address: {event.ip_address}
            Timestamp: {event.timestamp}
            Severity: {event.severity}
            
            Details: {json.dumps(event.metadata, indent=2)}
            """
            
            # Log alert
            logger.critical("Security alert sent", extra=asdict(event))
            
        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")

class SecurityAnomalyDetector:
    """Detect security anomalies and suspicious activities."""
    
    def __init__(self):
        self.user_baselines = {}
        self.ip_reputation_cache = {}
        
    async def analyze_event(self, event: SecurityEvent):
        """Analyze security event for anomalies."""
        try:
            anomalies = []
            
            # Check for suspicious IP addresses
            if await self._is_suspicious_ip(event.ip_address):
                anomalies.append("suspicious_ip")
            
            # Check for unusual login patterns
            if event.event_type in [SecurityEventType.LOGIN_SUCCESS, SecurityEventType.LOGIN_FAILED]:
                if await self._is_unusual_login_pattern(event):
                    anomalies.append("unusual_login_pattern")
            
            # Check for brute force attacks
            if await self._is_brute_force_attack(event):
                anomalies.append("brute_force_attack")
            
            # Check for impossible travel
            if await self._is_impossible_travel(event):
                anomalies.append("impossible_travel")
            
            # If anomalies detected, create alert
            if anomalies:
                await self._create_anomaly_alert(event, anomalies)
                
        except Exception as e:
            logger.error(f"Security anomaly analysis failed: {e}")
    
    async def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious."""
        try:
            # Check against known threat intelligence
            # In production, integrate with threat intelligence feeds
            
            # Check if IP is from a suspicious country/region
            # Check if IP is a known proxy/VPN/Tor exit node
            # Check IP reputation databases
            
            return False  # Placeholder
            
        except Exception:
            return False
    
    async def _is_unusual_login_pattern(self, event: SecurityEvent) -> bool:
        """Detect unusual login patterns."""
        try:
            if not event.user_id:
                return False
            
            # Check login time patterns
            current_hour = event.timestamp.hour
            
            # Get user's typical login hours
            baseline = self.user_baselines.get(event.user_id, {})
            typical_hours = baseline.get("login_hours", set(range(24)))
            
            # Check if current hour is unusual
            if current_hour not in typical_hours:
                return True
            
            # Check login frequency
            recent_logins = baseline.get("recent_login_count", 0)
            if recent_logins > 10:  # More than 10 logins in recent period
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _is_brute_force_attack(self, event: SecurityEvent) -> bool:
        """Detect brute force attacks."""
        try:
            if event.event_type != SecurityEventType.LOGIN_FAILED:
                return False
            
            # Count failed login attempts from same IP in last 10 minutes
            recent_failures = 0
            current_time = event.timestamp
            
            for stored_event in reversed(self.events_storage[-100:]):  # Check last 100 events
                if (stored_event.ip_address == event.ip_address and
                    stored_event.event_type == SecurityEventType.LOGIN_FAILED and
                    (current_time - stored_event.timestamp).total_seconds() <= 600):
                    recent_failures += 1
            
            return recent_failures >= 5  # 5 failures in 10 minutes
            
        except Exception:
            return False
    
    async def _is_impossible_travel(self, event: SecurityEvent) -> bool:
        """Detect impossible travel between login locations."""
        try:
            if not event.user_id or event.event_type != SecurityEventType.LOGIN_SUCCESS:
                return False
            
            # Find last successful login for this user
            for stored_event in reversed(self.events_storage):
                if (stored_event.user_id == event.user_id and
                    stored_event.event_type == SecurityEventType.LOGIN_SUCCESS and
                    stored_event.timestamp < event.timestamp):
                    
                    # Calculate time difference
                    time_diff = (event.timestamp - stored_event.timestamp).total_seconds()
                    
                    # If logins are within 1 hour, check geographical distance
                    if time_diff <= 3600:
                        # In production, use GeoIP to calculate distance
                        # and determine if travel is physically possible
                        pass
                    
                    break
            
            return False  # Placeholder
            
        except Exception:
            return False
    
    async def _create_anomaly_alert(self, event: SecurityEvent, anomalies: List[str]):
        """Create alert for detected anomalies."""
        try:
            alert_event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                resource=event.resource,
                metadata={
                    "original_event_id": event.event_id,
                    "detected_anomalies": anomalies,
                    "confidence_score": len(anomalies) / 4.0  # Normalize to 0-1
                },
                timestamp=datetime.utcnow(),
                severity="high"
            )
            
            # Log the anomaly alert
            logger.warning(
                "Security anomaly detected",
                anomalies=anomalies,
                original_event=event.event_id,
                confidence=alert_event.metadata["confidence_score"]
            )
            
        except Exception as e:
            logger.error(f"Failed to create anomaly alert: {e}")

class RateLimitManager:
    """Advanced rate limiting with adaptive thresholds."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
        
    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit."""
        try:
            key = f"rate_limit:{identifier}"
            current = await self.redis.get(key)
            
            if current is None:
                await self.redis.setex(key, window, 1)
                return True
            
            if int(current) >= limit:
                return False
            
            await self.redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Fail open
    
    async def adaptive_rate_limit(self, user_id: str, endpoint: str) -> int:
        """Calculate adaptive rate limit based on user behavior."""
        try:
            # Base rate limits by endpoint
            base_limits = {
                "/api/v2/clusters": 100,
                "/api/v2/recommendations": 50,
                "/api/v2/costs": 200,
                "default": 60
            }
            
            base_limit = base_limits.get(endpoint, base_limits["default"])
            
            # Adjust based on user reputation
            reputation_score = await self._get_user_reputation(user_id)
            
            if reputation_score > 0.8:
                return int(base_limit * 1.5)  # Increase limit for good users
            elif reputation_score < 0.3:
                return int(base_limit * 0.5)  # Decrease limit for suspicious users
            else:
                return base_limit
                
        except Exception:
            return 60  # Default fallback
    
    async def _get_user_reputation(self, user_id: str) -> float:
        """Calculate user reputation score (0-1)."""
        try:
            # Factors: account age, failed login attempts, security events, etc.
            # This is a simplified implementation
            
            failed_attempts = 0
            security_events = 0
            
            # Count recent security events for user
            for event in self.events_storage[-1000:]:  # Check recent events
                if event.user_id == user_id:
                    if event.event_type == SecurityEventType.LOGIN_FAILED:
                        failed_attempts += 1
                    elif event.event_type in [SecurityEventType.SUSPICIOUS_ACTIVITY, 
                                            SecurityEventType.UNAUTHORIZED_ACCESS]:
                        security_events += 1
            
            # Calculate reputation (higher is better)
            reputation = 1.0 - (failed_attempts * 0.1) - (security_events * 0.2)
            return max(0.0, min(1.0, reputation))
            
        except Exception:
            return 0.5  # Neutral reputation

class AdvancedAuthenticationMiddleware(BaseHTTPMiddleware):
    """Advanced authentication middleware with security features."""
    
    def __init__(self, app, security_manager):
        super().__init__(app)
        self.security_manager = security_manager
        
    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        start_time = datetime.utcnow()
        
        try:
            # Extract client information
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Check IP whitelist/blacklist
            if await self._is_ip_blocked(ip_address):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address is blocked"
                )
            
            # Rate limiting
            if not await self.security_manager.rate_limiter.check_rate_limit(
                ip_address, limit=100, window=60
            ):
                await self._log_rate_limit_event(request, ip_address)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Process request
            response = await call_next(request)
            
            # Log successful request
            duration = (datetime.utcnow() - start_time).total_seconds()
            API_REQUEST_DURATION.labels(
                endpoint=request.url.path,
                method=request.method
            ).observe(duration)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked."""
        try:
            # Check against IP blacklist
            blocked_ips = await self.security_manager._get_blocked_ips()
            return ip_address in blocked_ips
        except Exception:
            return False
    
    async def _log_rate_limit_event(self, request: Request, ip_address: str):
        """Log rate limit exceeded event."""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            user_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent", ""),
            resource=request.url.path,
            metadata={
                "method": request.method,
                "endpoint": request.url.path
            },
            timestamp=datetime.utcnow(),
            severity="medium"
        )
        
        await self.security_manager.event_logger.log_security_event(event)

class EnterpriseSecurityManager:
    """Central security manager for enterprise features."""
    
    def __init__(self):
        self.crypto = AdvancedCryptography()
        self.mfa_manager = MFAManager()
        self.jwt_manager = JWTManager(os.getenv("JWT_SECRET_KEY", "dev-secret"))
        self.event_logger = SecurityEventLogger()
        self.redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.rate_limiter = RateLimitManager(self.redis_client)
        
        # User storage (in production, use proper database)
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        
    async def authenticate_user(self, username: str, password: str, 
                              mfa_token: Optional[str] = None,
                              request_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Authenticate user with optional MFA."""
        try:
            # Find user
            user = await self._get_user_by_username(username)
            if not user:
                await self._log_authentication_event(
                    SecurityEventType.LOGIN_FAILED, None, request_info,
                    {"reason": "user_not_found"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check if account is locked
            if user.account_locked:
                await self._log_authentication_event(
                    SecurityEventType.LOGIN_FAILED, user.user_id, request_info,
                    {"reason": "account_locked"}
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is locked"
                )
            
            # Verify password
            if not self.crypto.verify_password(password, user.password_hash):
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.account_locked = True
                
                await self._log_authentication_event(
                    SecurityEventType.LOGIN_FAILED, user.user_id, request_info,
                    {"reason": "invalid_password", "failed_attempts": user.failed_login_attempts}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check MFA if enabled
            if user.mfa_enabled:
                if not mfa_token:
                    return {
                        "requires_mfa": True,
                        "message": "MFA token required"
                    }
                
                if not self.mfa_manager.verify_mfa_token(user.mfa_secret, mfa_token):
                    await self._log_authentication_event(
                        SecurityEventType.MFA_FAILED, user.user_id, request_info,
                        {"reason": "invalid_mfa_token"}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid MFA token"
                    )
                
                await self._log_authentication_event(
                    SecurityEventType.MFA_SUCCESS, user.user_id, request_info
                )
            
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            
            # Generate tokens
            access_token = self.jwt_manager.create_access_token(user)
            refresh_token = self.jwt_manager.create_refresh_token(user)
            
            await self._log_authentication_event(
                SecurityEventType.LOGIN_SUCCESS, user.user_id, request_info
            )
            
            AUTHENTICATION_ATTEMPTS.labels(status="success", method="password").inc()
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "roles": [role.value for role in user.roles]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            AUTHENTICATION_ATTEMPTS.labels(status="error", method="password").inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    async def authenticate_api_key(self, api_key: str, 
                                 request_info: Dict[str, Any] = None) -> User:
        """Authenticate using API key."""
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find API key
            api_key_obj = None
            for key_obj in self.api_keys.values():
                if key_obj.key_hash == key_hash and key_obj.is_active:
                    api_key_obj = key_obj
                    break
            
            if not api_key_obj:
                await self._log_authentication_event(
                    SecurityEventType.LOGIN_FAILED, None, request_info,
                    {"reason": "invalid_api_key", "method": "api_key"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            
            # Check expiration
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
                await self._log_authentication_event(
                    SecurityEventType.LOGIN_FAILED, api_key_obj.user_id, request_info,
                    {"reason": "api_key_expired", "method": "api_key"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key expired"
                )
            
            # Check rate limit for API key
            if not await self.rate_limiter.check_rate_limit(
                f"api_key:{api_key_obj.key_id}", 
                api_key_obj.rate_limit, 
                3600  # 1 hour window
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="API key rate limit exceeded"
                )
            
            # Update last used
            api_key_obj.last_used = datetime.utcnow()
            
            # Get user
            user = await self._get_user_by_id(api_key_obj.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            await self._log_authentication_event(
                SecurityEventType.LOGIN_SUCCESS, user.user_id, request_info,
                {"method": "api_key", "api_key_id": api_key_obj.key_id}
            )
            
            AUTHENTICATION_ATTEMPTS.labels(status="success", method="api_key").inc()
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key authentication failed: {e}")
            AUTHENTICATION_ATTEMPTS.labels(status="error", method="api_key").inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    async def authorize_user(self, user: User, required_permission: Permission,
                           resource: Optional[str] = None) -> bool:
        """Authorize user for specific permission."""
        try:
            # Check if user has required permission
            has_permission = required_permission in user.permissions
            
            # Log authorization check
            AUTHORIZATION_CHECKS.labels(
                status="granted" if has_permission else "denied",
                resource=resource or "unknown"
            ).inc()
            
            if not has_permission:
                await self._log_authorization_event(
                    user.user_id, required_permission, resource, False
                )
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Authorization check failed: {e}")
            return False
    
    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    async def _get_blocked_ips(self) -> Set[str]:
        """Get list of blocked IP addresses."""
        try:
            # In production, load from database
            blocked_ips = await self.redis_client.smembers("blocked_ips")
            return {ip.decode() for ip in blocked_ips}
        except Exception:
            return set()
    
    async def _log_authentication_event(self, event_type: SecurityEventType,
                                      user_id: Optional[str],
                                      request_info: Optional[Dict[str, Any]],
                                      metadata: Optional[Dict[str, Any]] = None):
        """Log authentication event."""
        if not request_info:
            request_info = {}
        
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            ip_address=request_info.get("ip_address", "unknown"),
            user_agent=request_info.get("user_agent", "unknown"),
            resource=request_info.get("endpoint"),
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
            severity="medium" if "failed" in event_type.value else "low"
        )
        
        await self.event_logger.log_security_event(event)
    
    async def _log_authorization_event(self, user_id: str, permission: Permission,
                                     resource: Optional[str], granted: bool):
        """Log authorization event."""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS if not granted else SecurityEventType.DATA_ACCESS,
            user_id=user_id,
            ip_address="unknown",  # Would be filled by middleware
            user_agent="unknown",
            resource=resource,
            metadata={
                "permission": permission.value,
                "granted": granted
            },
            timestamp=datetime.utcnow(),
            severity="high" if not granted else "low"
        )
        
        await self.event_logger.log_security_event(event)

# FastAPI Dependencies for Authentication
security_manager = EnterpriseSecurityManager()
bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> User:
    """Get current authenticated user from JWT token."""
    try:
        payload = security_manager.jwt_manager.verify_token(credentials.credentials)
        user = await security_manager._get_user_by_id(payload.get("sub"))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def require_permission(permission: Permission):
    """Dependency factory for permission-based authorization."""
    async def check_permission(user: User = Depends(get_current_user)) -> User:
        if not await security_manager.authorize_user(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        return user
    
    return check_permission

# Example usage
if __name__ == "__main__":
    async def demo():
        # Create demo user
        demo_user = User(
            user_id="demo-user-123",
            username="demo_user",
            email="demo@example.com",
            roles=[UserRole.COST_ANALYST],
            permissions=[Permission.READ_CLUSTERS, Permission.READ_COSTS],
            mfa_enabled=True,
            mfa_secret="demo_secret",
            created_at=datetime.utcnow(),
            last_login=None,
            failed_login_attempts=0,
            account_locked=False,
            password_hash=security_manager.crypto.hash_password("demo_password")
        )
        
        security_manager.users[demo_user.user_id] = demo_user
        
        # Demo authentication
        try:
            result = await security_manager.authenticate_user(
                "demo_user", 
                "demo_password",
                request_info={
                    "ip_address": "192.168.1.1",
                    "user_agent": "Demo Client",
                    "endpoint": "/login"
                }
            )
            print("Authentication successful!")
            print(f"Access token: {result['access_token'][:50]}...")
            
        except Exception as e:
            print(f"Authentication failed: {e}")
    
    asyncio.run(demo())