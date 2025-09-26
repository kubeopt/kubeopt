#!/usr/bin/env python3
"""
Feature Guard for AKS Cost Optimizer
===================================

Decorators and middleware for feature locking.
"""

import functools
from flask import jsonify, redirect, url_for, request, render_template_string
from infrastructure.services.license_manager import license_manager, FeatureFlag

def require_feature(feature: FeatureFlag, api_response: bool = False):
    """
    Decorator to require a specific feature to be enabled
    
    Args:
        feature: The required feature flag
        api_response: If True, return JSON response for API endpoints
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if license_manager.is_feature_enabled(feature):
                return func(*args, **kwargs)
            
            # Feature is locked
            if api_response:
                # API response
                return jsonify({
                    'status': 'error',
                    'error': 'feature_locked',
                    'message': f'This feature requires {get_required_tier(feature)} tier',
                    'feature': feature.value,
                    'current_tier': license_manager.get_current_tier().value,
                    'upgrade_info': license_manager.get_upgrade_info()
                }), 403
            else:
                # Web response - redirect to upgrade page or show locked page
                return render_feature_locked_page(feature)
                
        return wrapper
    return decorator

def get_required_tier(feature: FeatureFlag) -> str:
    """Get the minimum tier required for a feature"""
    tier_features = license_manager.tier_features
    
    for tier, features in tier_features.items():
        if feature in features:
            return tier.value.title()
    
    return "Pro"

def render_feature_locked_page(feature: FeatureFlag):
    """Render a feature locked page"""
    required_tier = get_required_tier(feature)
    current_tier = license_manager.get_current_tier().value.title()
    upgrade_info = license_manager.get_upgrade_info()
    
    locked_page_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Feature Locked - KUBEVISTA</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    </head>
    <body class="bg-gray-50 min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full mx-4">
            <div class="bg-white rounded-lg shadow-lg p-8 text-center">
                <!-- Lock Icon -->
                <div class="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <i class="fas fa-lock text-yellow-600 text-2xl"></i>
                </div>
                
                <!-- Title -->
                <h1 class="text-2xl font-bold text-gray-800 mb-2">Feature Locked</h1>
                <p class="text-gray-600 mb-6">This feature requires {{ required_tier }} tier</p>
                
                <!-- Current vs Required -->
                <div class="bg-gray-50 rounded-lg p-4 mb-6">
                    <div class="flex justify-between items-center text-sm">
                        <div>
                            <span class="text-gray-500">Current:</span>
                            <span class="font-semibold text-gray-700">{{ current_tier }}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Required:</span>
                            <span class="font-semibold text-blue-600">{{ required_tier }}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Feature Info -->
                <div class="text-left mb-6">
                    <h3 class="font-semibold text-gray-800 mb-2">{{ feature_display }} includes:</h3>
                    <ul class="text-sm text-gray-600 space-y-1">
                        {% for feature_desc in feature_descriptions %}
                        <li class="flex items-center">
                            <i class="fas fa-check text-green-500 mr-2"></i>
                            {{ feature_desc }}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                
                <!-- Action Buttons -->
                <div class="space-y-3">
                    <a href="/license/upgrade" class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center">
                        <i class="fas fa-arrow-up mr-2"></i>
                        Upgrade to {{ required_tier }}
                    </a>
                    <a href="/license/trial" class="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center">
                        <i class="fas fa-gift mr-2"></i>
                        Start Free Trial
                    </a>
                    <a href="/" class="w-full bg-gray-500 text-white py-3 px-4 rounded-lg hover:bg-gray-600 transition-colors flex items-center justify-center">
                        <i class="fas fa-arrow-left mr-2"></i>
                        Back to Dashboard
                    </a>
                </div>
                
                <!-- Contact -->
                <p class="text-xs text-gray-500 mt-6">
                    Questions? <a href="mailto:support@kubevista.com" class="text-blue-600 hover:underline">Contact Support</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Feature descriptions
    feature_descriptions = {
        FeatureFlag.IMPLEMENTATION_PLAN: [
            "Step-by-step optimization plans",
            "Automated implementation scripts", 
            "Best practices recommendations"
        ],
        FeatureFlag.AUTO_ANALYSIS: [
            "Scheduled automatic analysis",
            "Background processing",
            "Continuous monitoring"
        ],
        FeatureFlag.ENTERPRISE_METRICS: [
            "Advanced operational metrics",
            "Compliance readiness scores",
            "Team velocity tracking"
        ],
        FeatureFlag.SECURITY_POSTURE: [
            "Security vulnerability scanning",
            "Compliance framework analysis",
            "Policy recommendations"
        ],
        FeatureFlag.EMAIL_ALERTS: [
            "Email notifications",
            "Custom alert thresholds",
            "Scheduled reports"
        ]
    }
    
    feature_display = feature.value.replace('_', ' ').title()
    
    return render_template_string(
        locked_page_html,
        feature=feature.value,
        feature_display=feature_display,
        feature_descriptions=feature_descriptions.get(feature, ["Advanced functionality"]),
        required_tier=required_tier,
        current_tier=current_tier,
        upgrade_info=upgrade_info
    )

def check_feature_access(feature: FeatureFlag) -> dict:
    """Check if user has access to a feature and return status"""
    enabled = license_manager.is_feature_enabled(feature)
    
    return {
        'enabled': enabled,
        'feature': feature.value,
        'current_tier': license_manager.get_current_tier().value,
        'required_tier': get_required_tier(feature) if not enabled else None,
        'upgrade_info': license_manager.get_upgrade_info() if not enabled else None
    }

def get_ui_feature_flags() -> dict:
    """Get feature flags for UI rendering"""
    return {
        'dashboard': license_manager.is_feature_enabled(FeatureFlag.DASHBOARD),
        'implementation_plan': license_manager.is_feature_enabled(FeatureFlag.IMPLEMENTATION_PLAN),
        'auto_analysis': license_manager.is_feature_enabled(FeatureFlag.AUTO_ANALYSIS),
        'enterprise_metrics': license_manager.is_feature_enabled(FeatureFlag.ENTERPRISE_METRICS),
        'security_posture': license_manager.is_feature_enabled(FeatureFlag.SECURITY_POSTURE),
        'email_alerts': license_manager.is_feature_enabled(FeatureFlag.EMAIL_ALERTS),
        'slack_alerts': license_manager.is_feature_enabled(FeatureFlag.SLACK_ALERTS),
        'current_tier': license_manager.get_current_tier().value,
        'license_info': license_manager.get_license_info()
    }