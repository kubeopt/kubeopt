#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Authentication Routes for AKS Cost Optimizer
============================================

Handles login, logout, and settings management routes.
"""

import json
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from infrastructure.services.auth_manager import auth_manager
from infrastructure.services.settings_manager import settings_manager

logger = logging.getLogger(__name__)

def register_auth_routes(app):
    """Register authentication and settings routes"""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page and authentication"""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not password:
                flash('Please enter both username and password', 'error')
                return render_template('login.html')
            
            if auth_manager.authenticate_user(username, password):
                session_token = auth_manager.create_session(username)
                if session_token:
                    return redirect(url_for('cluster_portfolio'))
                else:
                    flash('Login successful but session creation failed', 'error')
            else:
                flash('Invalid username or password', 'error')
        
        # If already authenticated, redirect to dashboard
        if auth_manager.validate_session():
            return redirect(url_for('cluster_portfolio'))
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout and destroy session"""
        user = auth_manager.get_current_user()
        username = user.get('username', 'Unknown')
        
        auth_manager.destroy_session()
        flash(f'Session ended for {username}. Thank you for using kubeopt.', 'success')
        return redirect(url_for('login'))
    
    @app.route('/settings')
    @auth_manager.require_auth
    def settings():
        """Settings page"""
        if not auth_manager.is_admin():
            flash('Admin access required for settings', 'error')
            return redirect(url_for('cluster_portfolio'))
        
        try:
            # Get current configuration
            current_config = settings_manager.get_settings()
            
            # Get custom environment variables
            custom_env_vars = settings_manager.get_custom_env_vars()
            
            # Get feature flags for UI rendering
            from infrastructure.services.feature_guard import get_ui_feature_flags
            feature_flags = get_ui_feature_flags()
            
            # Get license information
            from infrastructure.services.license_manager import license_manager
            license_info = license_manager.get_license_info()
            
            return render_template('settings.html', 
                                 config=current_config,
                                 custom_env_vars=custom_env_vars,
                                 feature_flags=feature_flags,
                                 license_info=license_info)
        except Exception as e:
            logger.error(f"Error loading settings page: {e}")
            flash('Error loading settings', 'error')
            return redirect(url_for('cluster_portfolio'))
    
    @app.route('/save_settings', methods=['POST'])
    @auth_manager.require_auth
    def save_settings():
        """Save application settings"""
        if not auth_manager.is_admin():
            flash('Admin access required to save settings', 'error')
            return redirect(url_for('settings'))
        
        try:
            # Get section from form to determine which settings to save
            section = request.form.get('section', '').strip()
            settings_data = {}
            success_message = 'Settings saved successfully!'
            
            if section == 'azure':
                # Azure settings
                azure_fields = ['azure_tenant_id', 'azure_subscription_id', 'azure_client_id', 'azure_client_secret']
                for field in azure_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                success_message = 'Azure settings saved successfully!'
            
            elif section == 'slack':
                # Slack settings
                settings_data['slack_enabled'] = 'true' if request.form.get('slack_enabled') else 'false'
                slack_fields = ['slack_webhook_url', 'slack_channel', 'slack_cost_threshold']
                for field in slack_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                success_message = 'Slack settings saved successfully!'
            
            elif section == 'email':
                # Email settings
                settings_data['email_enabled'] = 'true' if request.form.get('email_enabled') else 'false'
                email_fields = ['smtp_server', 'smtp_port', 'email_username', 'email_password', 'email_recipients']
                for field in email_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                success_message = 'Email settings saved successfully!'
            
            elif section == 'general':
                # General settings
                general_fields = ['analysis_refresh_interval', 'cost_alert_threshold', 'log_level']
                for field in general_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                settings_data['production_mode'] = 'true' if request.form.get('production_mode') else 'false'
                
                # Handle license key activation
                license_key = request.form.get('license_key', '').strip()
                if license_key:
                    try:
                        from infrastructure.services.license_manager import license_manager
                        success, message = license_manager.activate_license(license_key)
                        if success:
                            success_message = f'General settings saved successfully! {message}'
                        else:
                            flash(f'License activation failed: {message}', 'error')
                            success_message = 'General settings saved successfully, but license activation failed.'
                    except Exception as e:
                        logger.error(f"Error activating license: {e}")
                        flash(f'License activation error: {str(e)}', 'error')
                        success_message = 'General settings saved successfully, but license activation failed.'
                else:
                    success_message = 'General settings saved successfully!'
            
            elif section == 'advanced':
                # Custom environment variables
                custom_env_vars = request.form.get('custom_env_vars', '').strip()
                if custom_env_vars:
                    settings_data['custom_env_vars'] = custom_env_vars
                success_message = 'Advanced settings saved successfully!'
            
            else:
                # Fallback to save all settings (for backwards compatibility)
                # Azure settings
                azure_fields = ['azure_tenant_id', 'azure_subscription_id', 'azure_client_id', 'azure_client_secret']
                for field in azure_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                
                # Slack settings
                settings_data['slack_enabled'] = 'true' if request.form.get('slack_enabled') else 'false'
                slack_fields = ['slack_webhook_url', 'slack_channel', 'slack_cost_threshold']
                for field in slack_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                
                # Email settings
                settings_data['email_enabled'] = 'true' if request.form.get('email_enabled') else 'false'
                email_fields = ['smtp_server', 'smtp_port', 'email_username', 'email_password', 'email_recipients']
                for field in email_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                
                # General settings
                general_fields = ['analysis_refresh_interval', 'cost_alert_threshold', 'log_level']
                for field in general_fields:
                    value = request.form.get(field, '').strip()
                    if value:
                        settings_data[field] = value
                settings_data['production_mode'] = 'true' if request.form.get('production_mode') else 'false'
                
                # Custom environment variables
                custom_env_vars = request.form.get('custom_env_vars', '').strip()
                if custom_env_vars:
                    settings_data['custom_env_vars'] = custom_env_vars
            
            # Save settings
            if settings_manager.save_settings(settings_data):
                # If Azure settings were saved, refresh Azure credentials
                if section == 'azure' or not section:
                    try:
                        from infrastructure.services.azure_sdk_manager import azure_sdk_manager
                        if azure_sdk_manager.refresh_credentials():
                            success_message += ' Azure credentials refreshed.'
                        else:
                            success_message += ' Note: Azure credential refresh failed - check your settings.'
                    except Exception as e:
                        logger.warning(f"Azure credential refresh failed: {e}")
                        success_message += ' Note: Azure credential refresh failed.'
                
                flash(success_message, 'success')
                logger.info(f"Settings ({section or 'all'}) updated by user: {auth_manager.get_current_user().get('username')}")
            else:
                flash('Error saving settings', 'error')
                
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            flash(f'Error saving settings: {str(e)}', 'error')
        
        return redirect(url_for('settings'))
    
    @app.route('/test_slack', methods=['POST'])
    @auth_manager.require_auth
    def test_slack():
        """Test Slack integration"""
        if not auth_manager.is_admin():
            return jsonify({'success': False, 'message': 'Admin access required'})
        
        try:
            result = settings_manager.test_slack_integration()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error testing Slack: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/test_email', methods=['POST'])
    @auth_manager.require_auth
    def test_email():
        """Test email configuration"""
        if not auth_manager.is_admin():
            return jsonify({'success': False, 'message': 'Admin access required'})
        
        try:
            smtp_server = request.form.get('smtp_server', '').strip()
            smtp_port = int(request.form.get('smtp_port', '587'))
            username = request.form.get('email_username', '').strip()
            password = request.form.get('email_password', '').strip()
            
            # Use current user's email as test recipient
            recipients = [username] if username else []
            
            if not all([smtp_server, username, password]):
                return jsonify({'success': False, 'message': 'Please fill in all email fields'})
            
            result = settings_manager.test_email_configuration(smtp_server, smtp_port, username, password, recipients)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error testing email: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/test_azure', methods=['POST'])
    @auth_manager.require_auth
    def test_azure():
        """Test Azure authentication"""
        if not auth_manager.is_admin():
            return jsonify({'success': False, 'message': 'Admin access required'})
        
        try:
            from infrastructure.services.azure_sdk_manager import azure_sdk_manager
            
            # Try to refresh credentials first with new settings
            refresh_success = azure_sdk_manager.refresh_credentials()
            
            if refresh_success and azure_sdk_manager.is_authenticated():
                subscription_id = azure_sdk_manager.get_subscription_id()
                if subscription_id:
                    return jsonify({
                        'success': True, 
                        'message': f'Azure authentication successful! Connected to subscription: {subscription_id[:8]}...'
                    })
                else:
                    # Organization-wide access - show capability instead of specific subscription
                    return jsonify({
                        'success': True, 
                        'message': 'Azure authentication successful! Organization-wide access enabled. Ready to discover subscriptions and clusters.'
                    })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Azure authentication failed. Please check your tenant ID, client ID, and client secret.'
                })
            
        except Exception as e:
            logger.error(f"Error testing Azure authentication: {e}")
            return jsonify({'success': False, 'message': f'Azure test failed: {str(e)}'})
    
    @app.route('/api/system_status')
    @auth_manager.require_auth
    def system_status():
        """Get system status information"""
        try:
            current_user = auth_manager.get_current_user()
            active_sessions = auth_manager.get_active_sessions_count()
            
            status = {
                'authenticated': True,
                'username': current_user.get('username'),
                'role': current_user.get('role'),
                'active_sessions': active_sessions,
                'session_created': current_user.get('created').isoformat() if current_user.get('created') else None,
                'last_activity': current_user.get('last_activity').isoformat() if current_user.get('last_activity') else None
            }
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Session cleanup background task
    @app.before_request
    def before_request():
        """Cleanup expired sessions before each request"""
        try:
            auth_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    logger.info("✅ Authentication routes registered successfully")