#!/usr/bin/env python3
"""
Feature Guard - License-Based Feature Access Control
====================================================
Ensures features are accessible based on license tier.
"""

import logging
from functools import wraps
from flask import g, jsonify
from typing import Dict, Any

from infrastructure.services.license_validator import (
    get_license_validator,
    LicenseTier,
    Feature
)

logger = logging.getLogger(__name__)

def require_feature(feature, api_response=False):
    """
    Decorator to require a specific feature for a route
    
    Args:
        feature: Feature enum or FeatureFlag string
        api_response: If True, return JSON errors (for API endpoints)
    
    Usage:
        @require_feature(Feature.AI_PLAN_GENERATION)
        def generate_plan():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Convert string feature flags to Feature enum if needed
            if isinstance(feature, str):
                # Map legacy feature flags to new Feature enum
                feature_map = {
                    'ai_plans': Feature.AI_PLAN_GENERATION,
                    'implementation_plan': Feature.AI_PLAN_GENERATION,
                    'basic_dashboard': Feature.DASHBOARD,
                    'cluster_analysis': Feature.CLUSTER_ANALYSIS,
                    'export_reports': Feature.EXPORT_REPORTS,
                    'email_alerts': Feature.EMAIL_ALERTS,
                    'slack_alerts': Feature.SLACK_ALERTS,
                    'cost_tracking': Feature.ADVANCED_ANALYTICS,
                    'multi_cluster': Feature.UNLIMITED_CLUSTERS,
                    'auto_analysis': Feature.CLUSTER_ANALYSIS,
                    'advanced_analytics': Feature.ADVANCED_ANALYTICS
                }
                feature_enum = feature_map.get(feature, Feature.DASHBOARD)
            else:
                feature_enum = feature
            
            # Get license info from g (set by middleware)
            if not hasattr(g, 'license_tier'):
                error_response = {
                    'error': 'License validation not performed',
                    'message': 'Internal error - license middleware not initialized'
                }
                if api_response:
                    return jsonify(error_response), 500
                return jsonify(error_response), 500
            
            validator = get_license_validator()
            
            if not validator.has_feature(feature_enum):
                tier = g.license_tier
                error_response = {
                    'error': 'Feature not available',
                    'feature': feature_enum.value if hasattr(feature_enum, 'value') else str(feature),
                    'current_tier': tier.value,
                    'message': f'Feature requires a higher license tier'
                }
                if api_response:
                    return jsonify(error_response), 403
                return jsonify(error_response), 403
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def get_ui_feature_flags() -> Dict[str, Any]:
    """
    Get feature flags for UI based on current license
    
    Returns:
        Dictionary of feature flags for the UI
    """
    validator = get_license_validator()
    tier = validator.get_tier()
    
    # Base features (NO FREE TIER - everything requires license)
    if tier == LicenseTier.NONE:
        return {
            'tier': 'NONE',
            'has_license': False,
            'can_add_clusters': False,  # Cannot add clusters without license
            'show_dashboard': False,
            'show_analysis': False,
            'show_alerts': False,
            'show_recommendations': False,
            'show_ai_plans': False,
            'show_export': False,
            'show_settings': True,  # Settings always accessible to add license
            'cluster_limit': 0,
            'message': 'PRO or ENTERPRISE license required'
        }
    
    # PRO tier features
    if tier == LicenseTier.PRO:
        return {
            'tier': 'PRO',
            'has_license': True,
            'can_add_clusters': True,  # Can add clusters with PRO license
            'show_dashboard': True,
            'show_analysis': True,
            'show_alerts': True,
            'show_recommendations': True,
            'show_ai_plans': False,  # Not for PRO
            'show_export': True,
            'show_settings': True,
            'cluster_limit': 5,
            'analyses_per_day': 50,
            'message': 'PRO features enabled'
        }
    
    # ENTERPRISE tier features
    if tier == LicenseTier.ENTERPRISE:
        plan_status = validator.get_plan_generation_status()
        return {
            'tier': 'ENTERPRISE',
            'has_license': True,
            'can_add_clusters': True,  # Can add clusters with ENTERPRISE license
            'show_dashboard': True,
            'show_analysis': True,
            'show_alerts': True,
            'show_recommendations': True,
            'show_ai_plans': True,
            'show_export': True,
            'show_settings': True,
            'show_advanced_analytics': True,
            'show_custom_integrations': True,
            'cluster_limit': -1,  # Unlimited
            'analyses_per_day': -1,  # Unlimited
            'ai_plans_available': plan_status.get('available', False),
            'ai_plans_remaining': plan_status.get('remaining', 0),
            'message': 'ENTERPRISE features enabled - unlimited access'
        }
    
    # Default (shouldn't happen)
    return {
        'tier': 'UNKNOWN',
        'has_license': False,
        'message': 'License status unknown'
    }

# For backward compatibility with old code
class FeatureFlag:
    """Legacy feature flags - deprecated, use Feature enum instead"""
    BASIC_DASHBOARD = "basic_dashboard"
    CLUSTER_ANALYSIS = "cluster_analysis"
    AI_PLANS = "ai_plans"
    EXPORT_REPORTS = "export_reports"
    EMAIL_ALERTS = "email_alerts"
    SLACK_ALERTS = "slack_alerts"
    IMPLEMENTATION_PLAN = "implementation_plan"
    AUTO_ANALYSIS = "auto_analysis"
    MULTI_CLUSTER = "multi_cluster"
    COST_TRACKING = "cost_tracking"
    ADVANCED_ANALYTICS = "advanced_analytics"