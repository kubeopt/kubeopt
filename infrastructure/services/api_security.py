#!/usr/bin/env python3
"""
API Security Module
===================
Provides JWT tokens, API key management, request signing, and rate limiting
for secure API communications.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeOpt
"""

import os
import jwt
import hmac
import time
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

class APISecurityManager:
    """
    Comprehensive API security manager with JWT, HMAC signing, and rate limiting
    """
    
    def __init__(self):
        # JWT Configuration
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        self.jwt_expiry_minutes = int(os.getenv('JWT_EXPIRY_MINUTES', '60'))
        
        # API Key Configuration
        self.api_key = os.getenv('KUBEOPT_API_KEY', self._generate_api_key())
        self.api_secret = os.getenv('KUBEOPT_API_SECRET', secrets.token_urlsafe(32))
        
        # Rate limiting storage
        self.rate_limit_storage = {}
        
        # HMAC signing key
        self.hmac_key = os.getenv('HMAC_SECRET_KEY', secrets.token_urlsafe(32)).encode()
        
        logger.info("API Security Manager initialized")
        if not os.getenv('JWT_SECRET_KEY'):
            logger.warning("Using auto-generated JWT secret - set JWT_SECRET_KEY in production!")
    
    def _generate_api_key(self) -> str:
        """Generate a new API key"""
        return f"ko_{secrets.token_urlsafe(24)}"
    
    # ==================== JWT Token Management ====================
    
    def generate_jwt_token(self, user_id: str, role: str = 'user', 
                          additional_claims: Dict[str, Any] = None) -> str:
        """
        Generate a JWT token for API authentication
        
        Args:
            user_id: User identifier
            role: User role (admin, user, readonly)
            additional_claims: Extra claims to include in token
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=self.jwt_expiry_minutes),
            'jti': secrets.token_urlsafe(16),  # JWT ID for tracking
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.debug(f"Generated JWT token for user: {user_id}")
        return token
    
    def verify_jwt_token(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Tuple of (is_valid, decoded_payload_or_error)
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            logger.debug(f"JWT token verified for user: {payload.get('user_id')}")
            return True, payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return False, {'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, {'error': 'Invalid token'}
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate a refresh token for extended sessions"""
        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=30),
            'jti': secrets.token_urlsafe(24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    # ==================== Request Signing (HMAC) ====================
    
    def sign_request(self, method: str, path: str, body: str = '', 
                     timestamp: Optional[int] = None) -> str:
        """
        Generate HMAC signature for a request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body as string
            timestamp: Unix timestamp (current time if not provided)
            
        Returns:
            Base64 encoded signature
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Create message to sign
        message = f"{method.upper()}:{path}:{timestamp}:{body}"
        
        # Generate HMAC
        signature = hmac.new(
            self.hmac_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Combine timestamp and signature
        signed_data = f"{timestamp}:{base64.b64encode(signature).decode()}"
        return base64.b64encode(signed_data.encode()).decode()
    
    def verify_request_signature(self, signature: str, method: str, 
                                path: str, body: str = '') -> bool:
        """
        Verify HMAC signature of a request
        
        Args:
            signature: Base64 encoded signature from request
            method: HTTP method
            path: Request path
            body: Request body
            
        Returns:
            True if signature is valid and not expired
        """
        try:
            # Decode signature
            decoded = base64.b64decode(signature.encode()).decode()
            timestamp_str, sig_b64 = decoded.split(':', 1)
            timestamp = int(timestamp_str)
            
            # Check if signature is not too old (5 minutes)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                logger.warning("Request signature expired")
                return False
            
            # Recreate and verify signature
            expected_sig = self.sign_request(method, path, body, timestamp)
            return hmac.compare_digest(signature, expected_sig)
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    # ==================== API Key Management ====================
    
    def generate_api_headers(self, include_jwt: bool = False, 
                            user_id: Optional[str] = None) -> Dict[str, str]:
        """
        Generate secure headers for API requests
        
        Args:
            include_jwt: Whether to include JWT token
            user_id: User ID for JWT generation
            
        Returns:
            Dictionary of headers
        """
        headers = {
            'X-API-Key': self.api_key,
            'X-Request-ID': secrets.token_urlsafe(16),
            'X-Timestamp': str(int(time.time()))
        }
        
        if include_jwt and user_id:
            token = self.generate_jwt_token(user_id)
            headers['Authorization'] = f"Bearer {token}"
        
        return headers
    
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify if provided API key is valid"""
        return hmac.compare_digest(provided_key, self.api_key)
    
    # ==================== Rate Limiting ====================
    
    def rate_limit(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Decorator for rate limiting API endpoints
        
        Args:
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Get client identifier (IP or API key)
                client_id = request.headers.get('X-API-Key', request.remote_addr)
                
                current_time = time.time()
                window_start = current_time - window_seconds
                
                # Initialize or get client's request history
                if client_id not in self.rate_limit_storage:
                    self.rate_limit_storage[client_id] = []
                
                # Clean old requests outside window
                self.rate_limit_storage[client_id] = [
                    req_time for req_time in self.rate_limit_storage[client_id]
                    if req_time > window_start
                ]
                
                # Check rate limit
                if len(self.rate_limit_storage[client_id]) >= max_requests:
                    logger.warning(f"Rate limit exceeded for client: {client_id}")
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window_seconds
                    }), 429
                
                # Add current request
                self.rate_limit_storage[client_id].append(current_time)
                
                return f(*args, **kwargs)
            return wrapped
        return decorator
    
    # ==================== Flask Decorators ====================
    
    def require_api_key(self, f):
        """Decorator to require valid API key for endpoint"""
        @wraps(f)
        def wrapped(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                logger.warning("Missing API key in request")
                return jsonify({'error': 'API key required'}), 401
            
            if not self.verify_api_key(api_key):
                logger.warning(f"Invalid API key: {api_key[:10]}...")
                return jsonify({'error': 'Invalid API key'}), 401
            
            return f(*args, **kwargs)
        return wrapped
    
    def require_jwt(self, f):
        """Decorator to require valid JWT token for endpoint"""
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                logger.warning("Missing or invalid Authorization header")
                return jsonify({'error': 'Bearer token required'}), 401
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            is_valid, payload = self.verify_jwt_token(token)
            
            if not is_valid:
                return jsonify(payload), 401
            
            # Add user info to request context
            request.jwt_payload = payload
            return f(*args, **kwargs)
        return wrapped
    
    def require_signed_request(self, f):
        """Decorator to require signed requests (HMAC)"""
        @wraps(f)
        def wrapped(*args, **kwargs):
            signature = request.headers.get('X-Signature')
            
            if not signature:
                logger.warning("Missing request signature")
                return jsonify({'error': 'Request signature required'}), 401
            
            # Get request details
            method = request.method
            path = request.path
            body = request.get_data(as_text=True) if request.data else ''
            
            if not self.verify_request_signature(signature, method, path, body):
                logger.warning("Invalid request signature")
                return jsonify({'error': 'Invalid signature'}), 401
            
            return f(*args, **kwargs)
        return wrapped

# Global instance
api_security = APISecurityManager()

# Export decorators for easy use
require_api_key = api_security.require_api_key
require_jwt = api_security.require_jwt
require_signed_request = api_security.require_signed_request
rate_limit = api_security.rate_limit