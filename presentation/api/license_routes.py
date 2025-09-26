#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
License Management Routes
=========================
Routes for license activation, upgrades, and tier management.
"""

from flask import render_template, request, jsonify, redirect, url_for, flash
from infrastructure.services.license_manager import license_manager, LicenseTier, FeatureFlag
from infrastructure.services.auth_manager import auth_manager
import logging

logger = logging.getLogger(__name__)

def register_license_routes(app):
    """Register license management routes"""
    
    @app.route('/license')
    @auth_manager.require_auth
    def license_overview():
        """License overview page - redirect to settings"""
        # Since license management is handled in settings, redirect there
        flash('License management is available in Settings', 'info')
        return redirect(url_for('settings'))
    
    @app.route('/license/upgrade')
    @auth_manager.require_auth
    def upgrade_page():
        """Redirect to external pricing page"""
        flash('Visit our pricing page to upgrade your license.', 'info')
        return redirect('https://kubevista.io/pricing')
    
    @app.route('/license/trial')
    @auth_manager.require_auth  
    def start_trial():
        """Start a free trial - redirect to clusters dashboard"""
        try:
            current_tier = license_manager.get_current_tier()
            
            if current_tier != LicenseTier.FREE:
                flash('You already have an active license.', 'info')
                return redirect(url_for('clusters'))
            
            # Generate a 30-day Pro trial
            trial_key = license_manager.generate_trial_license(LicenseTier.PRO, days=30)
            
            # Activate the trial
            success, message = license_manager.activate_license(trial_key)
            
            if success:
                flash('🎉 Pro trial activated! You now have access to Pro features for 30 days.', 'success')
                logger.info(f"✅ Pro trial started: {trial_key}")
            else:
                flash(f'Failed to activate trial: {message}', 'error')
                logger.error(f"❌ Failed to activate trial: {message}")
            
            # Redirect to clusters dashboard instead of license overview
            return redirect(url_for('clusters'))
            
        except Exception as e:
            logger.error(f"Error starting trial: {e}")
            flash(f'Error starting trial: {e}', 'error')
            return redirect(url_for('clusters'))
    
    @app.route('/license/activate', methods=['GET', 'POST'])
    @auth_manager.require_auth
    def activate_license():
        """License activation - redirect to settings"""
        if request.method == 'GET':
            flash('License activation is available in Settings.', 'info')
            return redirect(url_for('settings'))
        
        try:
            license_key = request.form.get('license_key', '').strip()
            
            if not license_key:
                flash('Please enter a license key.', 'error')
                return redirect(url_for('settings'))
            
            # Validate and activate license
            success, message = license_manager.activate_license(license_key)
            
            if success:
                flash(f'✅ License activated successfully! {message}', 'success')
                logger.info(f"✅ License activated: {license_key[:10]}...")
                return redirect(url_for('settings'))
            else:
                flash(f'❌ License activation failed: {message}', 'error')
                logger.error(f"❌ License activation failed: {message}")
                return redirect(url_for('settings'))
                
        except Exception as e:
            logger.error(f"Error activating license: {e}")
            flash(f'Error activating license: {e}', 'error')
            return redirect(url_for('settings'))
    
    @app.route('/api/license/info', methods=['GET'])
    @auth_manager.require_auth
    def api_license_info():
        """API endpoint for license information"""
        try:
            license_info = license_manager.get_license_info()
            upgrade_info = license_manager.get_upgrade_info()
            
            return jsonify({
                'status': 'success',
                'license': license_info,
                'upgrade_options': upgrade_info,
                'feature_flags': {
                    'dashboard': license_manager.is_feature_enabled(FeatureFlag.DASHBOARD),
                    'implementation_plan': license_manager.is_feature_enabled(FeatureFlag.IMPLEMENTATION_PLAN),
                    'auto_analysis': license_manager.is_feature_enabled(FeatureFlag.AUTO_ANALYSIS),
                    'enterprise_metrics': license_manager.is_feature_enabled(FeatureFlag.ENTERPRISE_METRICS),
                    'security_posture': license_manager.is_feature_enabled(FeatureFlag.SECURITY_POSTURE),
                    'email_alerts': license_manager.is_feature_enabled(FeatureFlag.EMAIL_ALERTS),
                    'slack_alerts': license_manager.is_feature_enabled(FeatureFlag.SLACK_ALERTS)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting license info: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/license/trial', methods=['POST'])
    @auth_manager.require_auth
    def api_start_trial():
        """API endpoint to start trial"""
        try:
            data = request.get_json() or {}
            tier = data.get('tier', 'pro').upper()
            days = int(data.get('days', 30))
            
            if tier not in ['PRO', 'ENTERPRISE']:
                return jsonify({
                    'status': 'error', 
                    'message': 'Invalid tier. Must be PRO or ENTERPRISE'
                }), 400
            
            current_tier = license_manager.get_current_tier()
            if current_tier != LicenseTier.FREE:
                return jsonify({
                    'status': 'error',
                    'message': 'You already have an active license'
                }), 400
            
            # Generate trial license
            trial_tier = LicenseTier.PRO if tier == 'PRO' else LicenseTier.ENTERPRISE
            trial_key = license_manager.generate_trial_license(trial_tier, days=days)
            
            # Activate trial
            success, message = license_manager.activate_license(trial_key)
            
            if success:
                logger.info(f"✅ {tier} trial started via API")
                return jsonify({
                    'status': 'success',
                    'message': f'{tier} trial activated for {days} days',
                    'license_info': license_manager.get_license_info()
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to activate trial: {message}'
                }), 500
                
        except Exception as e:
            logger.error(f"Error starting trial via API: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500