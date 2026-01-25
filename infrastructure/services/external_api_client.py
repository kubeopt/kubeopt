#!/usr/bin/env python3
"""
External API Client
===================
Handles communication with external License and Plan Generation APIs.
Supports both local development and production environments with enhanced security.
"""

import os
import json
import time
import hmac
import base64
import hashlib
import secrets
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class ExternalAPIClient:
    """Client for external KubeOpt APIs with enhanced security"""
    
    def __init__(self):
        """Initialize API client with configurable endpoints and security"""
        # Get API URLs from environment with defaults for local development
        self.license_api_url = os.getenv('LICENSE_API_URL', 'http://localhost:5002')
        self.plan_api_url = os.getenv('PLAN_API_URL', 'http://localhost:5003')
        
        # Get license key from environment
        self.license_key = os.getenv('KUBEOPT_LICENSE_KEY', '')
        
        # API Security Keys
        self.api_key = os.getenv('KUBEOPT_API_KEY', self._generate_api_key())
        self.api_secret = os.getenv('KUBEOPT_API_SECRET', secrets.token_urlsafe(32))
        
        # Timeout settings
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))
        self.plan_timeout = int(os.getenv('PLAN_API_TIMEOUT', '120'))  # Longer for Claude
        
        # Check if we're in local development mode
        self.local_mode = os.getenv('LOCAL_DEV', 'false').lower() == 'true'
        
        # Rate limiting
        self.request_history = {}
        self.rate_limit_max = int(os.getenv('API_RATE_LIMIT', '60'))
        self.rate_limit_window = int(os.getenv('API_RATE_WINDOW', '60'))
        
        logger.info(f"External API Client initialized:")
        logger.info(f"  License API: {self.license_api_url}")
        logger.info(f"  Plan API: {self.plan_api_url}")
        logger.info(f"  Local Mode: {self.local_mode}")
        logger.info(f"  API Key: {self.api_key[:10]}...")
        
        # Initialize encryption for sensitive data
        self.use_encryption = os.getenv('USE_LICENSE_ENCRYPTION', 'true').lower() == 'true'
        if self.use_encryption:
            self.encryption_key = self._derive_encryption_key()
            self.cipher = Fernet(self.encryption_key)
        else:
            logger.info("License encryption disabled - sending in plain text")
        
        if not os.getenv('KUBEOPT_API_SECRET'):
            logger.warning("Using auto-generated API secret - set KUBEOPT_API_SECRET in production!")
    
    def _generate_api_key(self) -> str:
        """Generate a new API key"""
        return f"ko_{secrets.token_urlsafe(24)}"
    
    def _derive_encryption_key(self) -> bytes:
        """
        Derive an encryption key from the API secret
        
        Returns:
            Fernet-compatible encryption key
        """
        # Use API secret as the basis for encryption
        password = self.api_secret.encode()
        salt = b'kubeopt_encryption_salt_2024'
        
        # Derive key using PBKDF2HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data for transmission
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            # Fallback to base64 encoding if encryption fails
            return base64.b64encode(data.encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data received from API
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted plain text
        """
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # Try base64 decode as fallback
            try:
                return base64.b64decode(encrypted_data.encode()).decode()
            except:
                return encrypted_data  # Return as-is if all fails
    
    def _check_rate_limit(self, endpoint: str) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            endpoint: API endpoint being called
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        # Initialize or clean request history for endpoint
        if endpoint not in self.request_history:
            self.request_history[endpoint] = []
        
        # Remove old requests outside window
        self.request_history[endpoint] = [
            req_time for req_time in self.request_history[endpoint]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.request_history[endpoint]) >= self.rate_limit_max:
            logger.warning(f"Rate limit exceeded for endpoint: {endpoint}")
            return False
        
        # Record this request
        self.request_history[endpoint].append(current_time)
        return True
    
    def _generate_request_signature(self, method: str, path: str, 
                                   body: Optional[Dict] = None) -> str:
        """
        Generate HMAC signature for request authentication
        
        Args:
            method: HTTP method
            path: API path
            body: Request body dictionary
            
        Returns:
            Base64 encoded signature
        """
        timestamp = str(int(time.time()))
        body_str = json.dumps(body, sort_keys=True) if body else ''
        
        # Create message to sign
        message = f"{method.upper()}:{path}:{timestamp}:{body_str}"
        
        # Generate HMAC
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combine timestamp and signature
        return base64.b64encode(f"{timestamp}:{signature}".encode()).decode()
    
    def _get_secure_headers(self, method: str = 'GET', path: str = '', 
                           body: Optional[Dict] = None) -> Dict[str, str]:
        """
        Generate secure headers for API requests
        
        Args:
            method: HTTP method
            path: API path
            body: Request body
            
        Returns:
            Dictionary of secure headers
        """
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'X-License-Key': self.license_key,
            'X-Request-ID': secrets.token_urlsafe(16),
            'X-Timestamp': str(int(time.time())),
            'X-Signature': self._generate_request_signature(method, path, body)
        }
        
        return headers
    
    def validate_license(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate the current license key with enhanced security
        
        Returns:
            Tuple of (is_valid, license_info)
        """
        if not self.license_key:
            logger.warning("No license key configured")
            if self.local_mode:
                # Allow local development without license
                return True, {
                    'tier': 'DEVELOPMENT',
                    'features': {
                        'basic_analysis': True,
                        'cost_reporting': True,
                        'ai_plans': True,
                        'auto_scheduling': True,
                        'multi_cluster': True
                    },
                    'limits': {
                        'clusters': -1,
                        'analyses_per_month': -1,
                        'ai_plans_per_month': -1
                    }
                }
            return False, {'error': 'No license key configured'}
        
        # Check rate limit
        endpoint = '/api/v1/validate'
        if not self._check_rate_limit(endpoint):
            return False, {'error': 'Rate limit exceeded', 'retry_after': self.rate_limit_window}
        
        try:
            # Prepare request with optionally encrypted license key
            url = f"{self.license_api_url}{endpoint}"
            
            if self.use_encryption:
                encrypted_key = self._encrypt_sensitive_data(self.license_key)
                body = {
                    'license_key': encrypted_key,
                    'encrypted': True  # Flag to indicate encrypted payload
                }
            else:
                # Send plain text for backward compatibility
                body = {'license_key': self.license_key}
            headers = self._get_secure_headers('POST', endpoint, body)
            
            # Make secure API call
            response = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=self.timeout,
                verify=not self.local_mode  # Skip SSL verification in local mode
            )
            
            if response.status_code == 200:
                license_info = response.json()
                logger.info(f"License validated: Tier={license_info.get('tier')}")
                return True, license_info
            elif response.status_code == 429:
                logger.warning("License API rate limit exceeded")
                return False, {'error': 'API rate limit exceeded', 'retry_after': 60}
            else:
                error_data = response.json() if response.text else {}
                logger.error(f"License validation failed: {error_data}")
                return False, error_data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to license API: {e}")
            if self.local_mode:
                logger.warning("Using development mode (license API unavailable)")
                return True, {
                    'tier': 'DEVELOPMENT',
                    'features': {'ai_plans': True},
                    'limits': {'ai_plans_per_month': -1}
                }
            return False, {'error': 'License service unavailable'}
    
    def generate_plan(self, cluster_id: str, cluster_name: str, 
                     analysis_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate an implementation plan via external API
        
        Args:
            cluster_id: Cluster identifier
            cluster_name: Cluster name
            analysis_data: Full analysis data from aks-cost-optimizer
            
        Returns:
            Tuple of (success, plan_data_or_error)
        """
        # First validate license
        is_valid, license_info = self.validate_license()
        
        if not is_valid:
            return False, {
                'error': 'Invalid or missing license',
                'details': license_info
            }
        
        # Check if license allows AI plans
        if not license_info.get('features', {}).get('ai_plans'):
            return False, {
                'error': 'Your license tier does not include AI plan generation',
                'tier': license_info.get('tier'),
                'upgrade_required': True
            }
        
        # Check rate limit for plan generation
        endpoint = '/plan-generation/v1/generate'
        if not self._check_rate_limit(endpoint):
            return False, {'error': 'Rate limit exceeded', 'retry_after': self.rate_limit_window}
        
        try:
            logger.info(f"Requesting plan generation for cluster {cluster_id}")
            
            # Prepare secure request with optionally encrypted license key
            url = f"{self.plan_api_url}{endpoint}"
            
            if self.use_encryption:
                encrypted_key = self._encrypt_sensitive_data(self.license_key)
                body = {
                    'license_key': encrypted_key,
                    'encrypted': True,  # Flag to indicate encrypted license key
                    'cluster_id': cluster_id,
                    'cluster_name': cluster_name,
                    'analysis_data': analysis_data
                }
            else:
                # Send plain text for backward compatibility
                body = {
                    'license_key': self.license_key,
                    'cluster_id': cluster_id,
                    'cluster_name': cluster_name,
                    'analysis_data': analysis_data
                }
            headers = self._get_secure_headers('POST', endpoint, body)
            
            # Make secure API call
            response = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=self.plan_timeout,
                verify=not self.local_mode  # Skip SSL verification in local mode
            )
            
            if response.status_code == 201:
                plan_data = response.json()
                logger.info(f"Plan generated successfully: {plan_data.get('plan_id')}")
                
                # Extract markdown from nested structure: plan.raw_markdown
                if isinstance(plan_data, dict) and 'plan' in plan_data:
                    nested_plan = plan_data.get('plan', {})
                    if isinstance(nested_plan, dict) and 'raw_markdown' in nested_plan:
                        # Copy the markdown to top level for easier access
                        plan_data['raw_markdown'] = nested_plan['raw_markdown']
                        logger.debug(f"Extracted markdown content from nested plan")
                    else:
                        logger.warning(f"Plan structure unexpected: no raw_markdown in nested plan")
                
                return True, plan_data
            else:
                error_data = response.json() if response.text else {}
                logger.error(f"Plan generation failed: {error_data}")
                return False, error_data
                
        except requests.exceptions.Timeout:
            logger.error("Plan generation timed out")
            return False, {'error': 'Plan generation timed out'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to plan generation API: {e}")
            return False, {'error': 'Plan generation service unavailable'}
    
    def get_license_status(self) -> Dict[str, Any]:
        """
        Get detailed license status including usage with enhanced security
        
        Returns:
            License status information
        """
        if not self.license_key:
            return {'error': 'No license key configured'}
        
        # Check rate limit
        endpoint = f'/api/v1/status/{self.license_key}'
        if not self._check_rate_limit(endpoint):
            return {'error': 'Rate limit exceeded', 'retry_after': self.rate_limit_window}
        
        try:
            # Prepare secure request
            url = f"{self.license_api_url}{endpoint}"
            headers = self._get_secure_headers('GET', endpoint)
            
            # Make secure API call
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=not self.local_mode  # Skip SSL verification in local mode
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                return {'error': 'API rate limit exceeded', 'retry_after': 60}
            else:
                return {'error': 'Failed to get license status'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get license status: {e}")
            return {'error': 'License service unavailable'}
    
    def check_feature_access(self, feature: str) -> bool:
        """
        Check if the current license has access to a specific feature
        
        Args:
            feature: Feature name (e.g., 'ai_plans', 'multi_cluster')
            
        Returns:
            True if feature is accessible
        """
        is_valid, license_info = self.validate_license()
        
        if not is_valid:
            return False
        
        features = license_info.get('features', {})
        return features.get(feature, False)
    
    def check_usage_limit(self, limit_type: str) -> Tuple[bool, int, int]:
        """
        Check usage against limits
        
        Args:
            limit_type: Type of limit (e.g., 'ai_plans_per_month')
            
        Returns:
            Tuple of (within_limit, current_usage, limit)
        """
        status = self.get_license_status()
        
        if 'error' in status:
            return False, 0, 0
        
        limits = status.get('limits', {})
        usage = status.get('usage', {})
        
        limit_value = limits.get(limit_type, 0)
        
        # Map limit type to usage field
        usage_mapping = {
            'ai_plans_per_month': 'plan_generations',
            'analyses_per_month': 'validations'
        }
        
        current_usage = usage.get(usage_mapping.get(limit_type, limit_type), 0)
        
        # -1 means unlimited
        if limit_value == -1:
            return True, current_usage, -1
        
        return current_usage < limit_value, current_usage, limit_value

# Global client instance
_client = None

def get_external_api_client() -> ExternalAPIClient:
    """Get or create the external API client singleton"""
    global _client
    if _client is None:
        _client = ExternalAPIClient()
    return _client