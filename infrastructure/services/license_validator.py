#!/usr/bin/env python3
"""
License Validator for AKS Cost Optimizer
=========================================
Single source of truth for license validation through external License Manager API.
NO FREE TIER - All features require PRO or ENTERPRISE license.
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
from enum import Enum
from functools import wraps
import json

logger = logging.getLogger(__name__)

class LicenseTier(Enum):
    """License tiers - NO FREE TIER"""
    NONE = "none"  # No license - no access
    PRO = "pro"
    ENTERPRISE = "enterprise"

class Feature(Enum):
    """Feature flags for different capabilities"""
    # PRO Features (Basic access)
    DASHBOARD = "dashboard"
    CLUSTER_ANALYSIS = "cluster_analysis"
    COST_REPORTING = "cost_reporting"
    EMAIL_ALERTS = "email_alerts"
    SLACK_ALERTS = "slack_alerts"
    BASIC_RECOMMENDATIONS = "basic_recommendations"
    EXPORT_REPORTS = "export_reports"
    
    # ENTERPRISE Features (Advanced)
    AI_PLAN_GENERATION = "ai_plan_generation"
    UNLIMITED_CLUSTERS = "unlimited_clusters"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_INTEGRATIONS = "custom_integrations"
    WHITE_LABEL = "white_label"
    API_ACCESS = "api_access"
    PRIORITY_SUPPORT = "priority_support"

class LicenseValidator:
    """
    Validates licenses through external License Manager API.
    Caches validation results and tracks usage limits.
    """
    
    # Feature mapping by tier
    TIER_FEATURES = {
        LicenseTier.NONE: [],
        LicenseTier.PRO: [
            Feature.DASHBOARD,
            Feature.CLUSTER_ANALYSIS,
            Feature.COST_REPORTING,
            Feature.EMAIL_ALERTS,
            Feature.SLACK_ALERTS,
            Feature.BASIC_RECOMMENDATIONS,
            Feature.EXPORT_REPORTS,
        ],
        LicenseTier.ENTERPRISE: [
            # All PRO features
            Feature.DASHBOARD,
            Feature.CLUSTER_ANALYSIS,
            Feature.COST_REPORTING,
            Feature.EMAIL_ALERTS,
            Feature.SLACK_ALERTS,
            Feature.BASIC_RECOMMENDATIONS,
            Feature.EXPORT_REPORTS,
            # Plus ENTERPRISE features
            Feature.AI_PLAN_GENERATION,
            Feature.UNLIMITED_CLUSTERS,
            Feature.ADVANCED_ANALYTICS,
            Feature.CUSTOM_INTEGRATIONS,
            Feature.WHITE_LABEL,
            Feature.API_ACCESS,
            Feature.PRIORITY_SUPPORT,
        ]
    }
    
    # Usage limits by tier
    TIER_LIMITS = {
        LicenseTier.NONE: {
            'clusters': 0,
            'analyses_per_day': 0,
            'plans_per_day': 0,
            'api_calls_per_hour': 0
        },
        LicenseTier.PRO: {
            'clusters': 5,
            'analyses_per_day': 50,
            'plans_per_day': 0,  # No AI plans for PRO
            'api_calls_per_hour': 100
        },
        LicenseTier.ENTERPRISE: {
            'clusters': -1,  # Unlimited
            'analyses_per_day': -1,  # Unlimited
            'plans_per_day': 1,  # One AI plan per day by default
            'api_calls_per_hour': -1  # Unlimited
        }
    }
    
    def __init__(self):
        self.license_api_url = os.getenv('LICENSE_API_URL', 'http://localhost:5002')
        self.license_key = os.getenv('KUBEOPT_LICENSE_KEY', '')
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.usage_tracker = {}  # Track daily usage
        
        # Initialize with validation
        if not self.license_key:
            logger.warning("No license key configured - all features disabled")
        else:
            logger.info(f"License validator initialized with key: {self.license_key[:10]}...")
    
    def validate_license(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate the current license key with external API
        
        Returns:
            Tuple[bool, Dict]: (is_valid, license_info)
        """
        if not self.license_key:
            return False, {
                'error': 'No license key configured',
                'tier': LicenseTier.NONE.value
            }
        
        # Check cache first
        cache_key = f"license:{self.license_key}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached['expires'] > datetime.now():
                return cached['valid'], cached['info']
        
        try:
            # Call License Manager API
            response = requests.post(
                f"{self.license_api_url}/api/v1/validate",
                json={'license_key': self.license_key},
                timeout=5
            )
            
            if response.status_code == 200:
                license_info = response.json()
                
                # Cache the result
                self.cache[cache_key] = {
                    'valid': True,
                    'info': license_info,
                    'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
                }
                
                return True, license_info
            else:
                error_info = {'error': 'Invalid license', 'tier': LicenseTier.NONE.value}
                if response.text:
                    try:
                        error_info = response.json()
                    except:
                        pass
                
                # Cache invalid result (shorter TTL)
                self.cache[cache_key] = {
                    'valid': False,
                    'info': error_info,
                    'expires': datetime.now() + timedelta(seconds=60)
                }
                
                return False, error_info
                
        except Exception as e:
            logger.error(f"Failed to validate license: {e}")
            return False, {
                'error': 'License validation failed',
                'details': str(e),
                'tier': LicenseTier.NONE.value
            }
    
    def get_tier(self) -> LicenseTier:
        """Get the current license tier"""
        valid, info = self.validate_license()
        if not valid:
            return LicenseTier.NONE
        
        tier_str = info.get('tier', 'none').upper()
        
        if tier_str == 'ENTERPRISE':
            return LicenseTier.ENTERPRISE
        elif tier_str == 'PRO':
            return LicenseTier.PRO
        else:
            return LicenseTier.NONE
    
    def has_feature(self, feature: Feature) -> bool:
        """Check if current license has access to a feature"""
        tier = self.get_tier()
        return feature in self.TIER_FEATURES.get(tier, [])
    
    def check_usage_limit(self, resource: str, count: int = 1) -> Tuple[bool, str]:
        """
        Check if usage is within limits
        
        Args:
            resource: Type of resource (clusters, analyses_per_day, plans_per_day)
            count: Number to check against limit
            
        Returns:
            Tuple[bool, str]: (within_limits, error_message)
        """
        tier = self.get_tier()
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS[LicenseTier.NONE])
        
        limit = limits.get(resource, 0)
        
        # -1 means unlimited
        if limit == -1:
            return True, ""
        
        # Track daily usage for per-day limits
        if 'per_day' in resource:
            today = datetime.now().date().isoformat()
            usage_key = f"{self.license_key}:{resource}:{today}"
            
            current_usage = self.usage_tracker.get(usage_key, 0)
            
            if current_usage + count > limit:
                return False, f"Daily limit reached for {resource}: {limit} per day"
            
            # Update usage tracker
            self.usage_tracker[usage_key] = current_usage + count
            
            # Clean old entries
            self._cleanup_usage_tracker()
        
        # For non-daily limits, just check the count
        elif count > limit:
            return False, f"Limit exceeded for {resource}: maximum {limit}"
        
        return True, ""
    
    def _cleanup_usage_tracker(self):
        """Remove old usage tracking entries"""
        today = datetime.now().date()
        old_keys = []
        
        for key in self.usage_tracker:
            if ':' in key:
                parts = key.split(':')
                if len(parts) >= 3:
                    try:
                        date_str = parts[-1]
                        entry_date = datetime.fromisoformat(date_str).date()
                        if (today - entry_date).days > 7:  # Keep 7 days of history
                            old_keys.append(key)
                    except:
                        pass
        
        for key in old_keys:
            del self.usage_tracker[key]
    
    def get_plan_generation_status(self) -> Dict[str, Any]:
        """
        Check if AI plan generation is available today
        
        Returns:
            Dict with status, available flag, and next reset time
        """
        tier = self.get_tier()
        
        if tier != LicenseTier.ENTERPRISE:
            return {
                'available': False,
                'reason': 'AI plan generation requires ENTERPRISE license',
                'tier': tier.value
            }
        
        # Check daily limit
        today = datetime.now().date().isoformat()
        usage_key = f"{self.license_key}:plans_per_day:{today}"
        current_usage = self.usage_tracker.get(usage_key, 0)
        
        daily_limit = self.TIER_LIMITS[LicenseTier.ENTERPRISE]['plans_per_day']
        
        if current_usage >= daily_limit:
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            
            return {
                'available': False,
                'reason': f'Daily plan generation limit reached ({daily_limit} per day)',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'next_reset': tomorrow_midnight.isoformat(),
                'hours_until_reset': (tomorrow_midnight - datetime.now()).total_seconds() / 3600
            }
        
        return {
            'available': True,
            'remaining': daily_limit - current_usage,
            'daily_limit': daily_limit,
            'current_usage': current_usage
        }
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get comprehensive license information"""
        valid, info = self.validate_license()
        tier = self.get_tier()
        
        if not valid:
            return {
                'valid': False,
                'tier': LicenseTier.NONE.value,
                'features': [],
                'limits': self.TIER_LIMITS[LicenseTier.NONE],
                'error': info.get('error', 'Invalid license')
            }
        
        # Get current usage
        today = datetime.now().date().isoformat()
        analyses_today = self.usage_tracker.get(f"{self.license_key}:analyses_per_day:{today}", 0)
        plans_today = self.usage_tracker.get(f"{self.license_key}:plans_per_day:{today}", 0)
        
        return {
            'valid': True,
            'tier': tier.value,
            'customer': info.get('customer', 'Unknown'),
            'expires_at': info.get('expires_at'),
            'days_remaining': info.get('days_remaining', -1),
            'features': [f.value for f in self.TIER_FEATURES[tier]],
            'limits': self.TIER_LIMITS[tier],
            'usage': {
                'analyses_today': analyses_today,
                'plans_today': plans_today
            }
        }

# Global instance
_validator = None

def get_license_validator() -> LicenseValidator:
    """Get or create the global license validator instance"""
    global _validator
    if _validator is None:
        _validator = LicenseValidator()
    return _validator

def require_license(min_tier: LicenseTier = LicenseTier.PRO):
    """
    Decorator to require a minimum license tier for a route
    
    Usage:
        @require_license(LicenseTier.PRO)
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            validator = get_license_validator()
            tier = validator.get_tier()
            
            if tier == LicenseTier.NONE:
                return {
                    'error': 'No valid license found',
                    'message': 'This feature requires a PRO or ENTERPRISE license'
                }, 401
            
            if tier.value < min_tier.value:
                return {
                    'error': 'Insufficient license tier',
                    'required': min_tier.value,
                    'current': tier.value,
                    'message': f'This feature requires {min_tier.value.upper()} license'
                }, 403
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def require_feature(feature: Feature):
    """
    Decorator to require a specific feature
    
    Usage:
        @require_feature(Feature.AI_PLAN_GENERATION)
        def generate_plan():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            validator = get_license_validator()
            
            if not validator.has_feature(feature):
                tier = validator.get_tier()
                return {
                    'error': 'Feature not available',
                    'feature': feature.value,
                    'current_tier': tier.value,
                    'message': f'Feature "{feature.value}" is not available in your license tier'
                }, 403
            
            return f(*args, **kwargs)
        return wrapped
    return decorator