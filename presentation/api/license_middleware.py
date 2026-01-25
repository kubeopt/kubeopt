#!/usr/bin/env python3
"""
License Middleware for AKS Cost Optimizer API
==============================================
Enforces license requirements on all API routes.
NO FREE ACCESS - All routes require at least PRO license.
"""

import logging
from flask import request, jsonify, g
from functools import wraps
from infrastructure.services.license_validator import (
    get_license_validator, 
    LicenseTier, 
    Feature
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Public routes that don't require license
# These allow users to navigate, login, and enter their license
PUBLIC_ROUTES = [
    '/health',
    '/api/health',
    '/api/v1/license/validate',  # License validation endpoint itself
    '/api/v1/license/info',
    '/static/',  # Static files
    '/login',    # Allow login page
    '/logout',   # Allow logout
    '/settings', # CRITICAL: Allow settings page for license entry
    '/',         # Allow landing/clusters page (read-only view)
    '/clusters', # Alternative clusters route
    '/api/v1/clusters',  # Allow GET for viewing clusters (empty state)
    '/api/v1/settings',  # Allow settings API
    '/api/auth/',        # Authentication endpoints
]

def check_license():
    """
    Middleware to check license on every request.
    Should be called before each request in Flask.
    """
    # Get license validator
    validator = get_license_validator()
    
    # Always store license info in g for use in routes
    g.license_info = validator.get_license_info()
    g.license_tier = validator.get_tier()
    
    logger.debug(f"License check for {request.method} {request.path} - tier: {g.license_tier}")
    
    # CRITICAL: Check cluster operations FIRST before public routes
    # This ensures POST /api/clusters is blocked even though GET /api/clusters might be allowed
    if request.path == '/api/clusters' and request.method == 'POST':
        logger.info(f"Checking license for POST /api/clusters - tier: {g.license_tier}")
        if g.license_tier == LicenseTier.NONE:
            logger.warning("Blocking cluster addition - no license")
            return jsonify({
                'error': 'License required to add clusters',
                'message': 'Please add a PRO or ENTERPRISE license in Settings to add clusters.',
                'current_tier': 'none',
                'required_tier': 'PRO'
            }), 403
        else:
            logger.info(f"Allowing POST /api/clusters for licensed user with tier: {g.license_tier}")
    
    # Skip license check for public routes
    for public_route in PUBLIC_ROUTES:
        if request.path.startswith(public_route):
            logger.debug(f"Skipping license check for public route: {request.path} matches {public_route}")
            # Even for public routes, set the tier info so pages can show appropriate UI
            return None
    
    # For API endpoints that modify data (POST, PUT, DELETE), require license
    if '/api/' in request.path and request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        if g.license_tier == LicenseTier.NONE:
            return jsonify({
                'error': 'License required for this action',
                'message': 'Please add a valid license in Settings to perform this action.',
                'current_tier': 'none',
                'required_tier': 'PRO'
            }), 403
    
    # Also block specific GET APIs that should require license
    protected_apis = [
        '/api/v1/add-cluster',    # Adding cluster endpoint
        '/api/v1/analyze',        # Running analysis
        '/api/v1/optimize',       # Getting optimizations
        '/api/v1/generate-plan'   # Generating plans
    ]
    
    for protected_api in protected_apis:
        if request.path.startswith(protected_api):
            if g.license_tier == LicenseTier.NONE:
                return jsonify({
                    'error': 'License required',
                    'message': 'This API requires a valid license.',
                    'current_tier': 'none',
                    'required_tier': 'PRO'
                }), 403
    
    # Protected pages that require a license to view
    protected_pages = [
        '/add-cluster',      # Cannot add clusters without license
        '/dashboard',        # Dashboard requires license
        '/analysis',         # Analysis page requires license  
        '/optimize',         # Optimization requires license
        '/alerts',           # Alerts require license
        '/implementation'    # Implementation plans require license
    ]
    
    for protected_page in protected_pages:
        if request.path.startswith(protected_page):
            if g.license_tier == LicenseTier.NONE:
                # For HTML pages, redirect to settings with message
                if request.path == '/add-cluster':
                    from flask import redirect, url_for, flash
                    flash('Please add a valid license in Settings to add clusters', 'warning')
                    return redirect(url_for('settings'))
                return jsonify({
                    'error': 'License required',
                    'message': 'This feature requires a PRO or ENTERPRISE license. Please add a license in Settings.',
                    'current_tier': 'none',
                    'required_tier': 'PRO'
                }), 403
    
    # Log access for licensed users
    if g.license_tier != LicenseTier.NONE:
        logger.info(f"Request from {g.license_info.get('customer', 'Unknown')} ({g.license_tier.value}): {request.method} {request.path}")
    
    return None

def init_license_middleware(app):
    """
    Initialize license middleware for Flask app
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        """Check license before every request"""
        error_response = check_license()
        if error_response:
            return error_response
    
    @app.route('/api/v1/license/info', methods=['GET'])
    def get_license_info():
        """Get current license information"""
        validator = get_license_validator()
        return jsonify(validator.get_license_info())
    
    @app.route('/api/v1/license/validate', methods=['POST'])
    def validate_license():
        """Validate a license key"""
        data = request.json or {}
        license_key = data.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'License key required'}), 400
        
        # Temporarily set the license key for validation
        import os
        old_key = os.environ.get('KUBEOPT_LICENSE_KEY', '')
        os.environ['KUBEOPT_LICENSE_KEY'] = license_key
        
        # Validate
        validator = get_license_validator()
        validator.license_key = license_key  # Update instance
        valid, info = validator.validate_license()
        
        # Restore old key
        if old_key:
            os.environ['KUBEOPT_LICENSE_KEY'] = old_key
        else:
            del os.environ['KUBEOPT_LICENSE_KEY']
        
        if valid:
            return jsonify({
                'valid': True,
                'tier': info.get('tier'),
                'features': info.get('features'),
                'expires_at': info.get('expires_at')
            })
        else:
            return jsonify({
                'valid': False,
                'error': info.get('error', 'Invalid license')
            }), 401
    
    logger.info("License middleware initialized - all routes protected")