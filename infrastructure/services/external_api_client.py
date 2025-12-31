#!/usr/bin/env python3
"""
External API Client
===================
Handles communication with external License and Plan Generation APIs.
Supports both local development and production environments.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ExternalAPIClient:
    """Client for external KubeOpt APIs"""
    
    def __init__(self):
        """Initialize API client with configurable endpoints"""
        # Get API URLs from environment with defaults for local development
        self.license_api_url = os.getenv('LICENSE_API_URL', 'http://localhost:5002')
        self.plan_api_url = os.getenv('PLAN_API_URL', 'http://localhost:5003')
        
        # Get license key from environment
        self.license_key = os.getenv('KUBEOPT_LICENSE_KEY', '')
        
        # Timeout settings
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))
        self.plan_timeout = int(os.getenv('PLAN_API_TIMEOUT', '120'))  # Longer for Claude
        
        # Check if we're in local development mode
        self.local_mode = os.getenv('LOCAL_DEV', 'false').lower() == 'true'
        
        logger.info(f"External API Client initialized:")
        logger.info(f"  License API: {self.license_api_url}")
        logger.info(f"  Plan API: {self.plan_api_url}")
        logger.info(f"  Local Mode: {self.local_mode}")
    
    def validate_license(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate the current license key
        
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
        
        try:
            response = requests.post(
                f"{self.license_api_url}/license/v1/validate",
                json={'license_key': self.license_key},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                license_info = response.json()
                logger.info(f"License validated: Tier={license_info.get('tier')}")
                return True, license_info
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
        
        try:
            logger.info(f"Requesting plan generation for cluster {cluster_id}")
            
            response = requests.post(
                f"{self.plan_api_url}/plan-generation/v1/generate",
                json={
                    'license_key': self.license_key,
                    'cluster_id': cluster_id,
                    'cluster_name': cluster_name,
                    'analysis_data': analysis_data
                },
                timeout=self.plan_timeout
            )
            
            if response.status_code == 201:
                plan_data = response.json()
                logger.info(f"Plan generated successfully: {plan_data.get('plan_id')}")
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
        Get detailed license status including usage
        
        Returns:
            License status information
        """
        if not self.license_key:
            return {'error': 'No license key configured'}
        
        try:
            response = requests.get(
                f"{self.license_api_url}/license/v1/status/{self.license_key}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
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