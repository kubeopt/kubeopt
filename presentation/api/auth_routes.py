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
    
    # Settings API endpoints (must be before login route)
    @app.route('/api/settings/save', methods=['POST'])
    def save_single_setting():
        """Save a single setting via auto-save"""
        try:
            from infrastructure.services.settings_manager import settings_manager
            data = request.get_json()
            
            if not data or 'key' not in data or 'value' not in data:
                return jsonify({'error': 'Missing key or value'}), 400
            
            key = data['key']
            value = data['value']
            
            # Special handling for license key
            if key == 'KUBEOPT_LICENSE_KEY' or key == 'license_key':
                if not value or len(value) < 10:
                    return jsonify({'error': 'Invalid license key'}), 400
                    
                from infrastructure.services.license_validator import get_license_validator
                validator = get_license_validator()
                validator.set_license_key(value)
                
                # Validate the license
                valid, info = validator.validate_license()
                if not valid:
                    error_msg = info.get('error', 'Invalid license key')
                    return jsonify({'error': f'License validation failed: {error_msg}'}), 400
                    
                settings_to_save = {'KUBEOPT_LICENSE_KEY': value}
                settings_manager.save_settings(settings_to_save)
                
                tier = info.get('tier', 'UNKNOWN')
                return jsonify({
                    'success': True, 
                    'message': f'License activated: {tier}',
                    'license_info': info
                })
            else:
                # Normal setting - ensure key is uppercase for .env
                env_key = key.upper() if not key.isupper() else key
                settings_to_save = {env_key: str(value)}
                settings_manager.save_settings(settings_to_save)
                
                return jsonify({
                    'success': True,
                    'message': f'{key} saved successfully'
                })
                
        except Exception as e:
            logger.error(f"Error saving setting: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/settings', methods=['GET', 'POST'])
    def settings_api():
        """Get or update settings as JSON"""
        if request.method == 'GET':
            try:
                from infrastructure.services.settings_manager import settings_manager
                settings = settings_manager.get_all_settings()
                
                # Add license info
                from infrastructure.services.license_validator import get_license_validator
                validator = get_license_validator()
                license_info = validator.get_license_info()
                
                # Mask sensitive values
                if 'kubeopt_license_key' in settings:
                    key = settings.get('kubeopt_license_key', '')
                    if key and len(key) > 10:
                        settings['license_key'] = f"{key[:10]}...****"
                    else:
                        settings['license_key'] = key
                
                return jsonify({
                    **settings,
                    'license': license_info
                })
            except Exception as e:
                logger.error(f"Error getting settings: {e}")
                return jsonify({'error': str(e)}), 500
        
        else:  # POST
            try:
                from infrastructure.services.settings_manager import settings_manager
                data = request.get_json()
                
                # Prepare settings dictionary for saving
                settings_to_save = {}
                
                # Process each setting
                for key, value in data.items():
                    # Special handling for license key
                    if key == 'KUBEOPT_LICENSE_KEY' or key == 'license_key':
                        # Activate license
                        from infrastructure.services.license_validator import get_license_validator
                        validator = get_license_validator()
                        validator.set_license_key(value)
                        settings_to_save['KUBEOPT_LICENSE_KEY'] = value
                    else:
                        # Ensure key is uppercase for .env
                        env_key = key.upper() if not key.isupper() else key
                        settings_to_save[env_key] = str(value)
                
                # Save all settings to .env file
                settings_manager.save_settings(settings_to_save)
                
                return jsonify({'status': 'success', 'message': 'Settings updated'})
            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/license/status', methods=['GET'])
    def license_status():
        """Get current license status"""
        try:
            from infrastructure.services.license_validator import get_license_validator
            from infrastructure.services.feature_guard import get_ui_feature_flags
            
            validator = get_license_validator()
            license_info = validator.get_license_info()
            feature_flags = get_ui_feature_flags()
            
            return jsonify({
                'tier': license_info.get('tier', 'NONE'),
                'has_license': license_info.get('tier') != 'NONE',
                'features': feature_flags,
                'license_info': license_info
            })
        except Exception as e:
            logger.error(f"Error getting license status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/get_settings', methods=['GET'])
    def get_settings_legacy():
        """Legacy endpoint for getting settings"""
        return settings_api()
    
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
            from infrastructure.services.license_validator import get_license_validator
            import os
            validator = get_license_validator()
            license_info = validator.get_license_info()
            
            # Add the masked license key for display
            current_license = os.getenv('KUBEOPT_LICENSE_KEY', '')
            if current_license:
                # Mask the middle part of the license key
                parts = current_license.split('-')
                if len(parts) >= 4:
                    # Show format like: PRO-U62B****-74B8
                    masked_parts = [parts[0]]  # Keep tier prefix
                    for i in range(1, len(parts)-1):
                        masked_parts.append(parts[i][:4] + '****' if len(parts[i]) > 4 else '****')
                    masked_parts.append(parts[-1])  # Keep last segment
                    masked = '-'.join(masked_parts)
                else:
                    # Fallback masking
                    masked = f"{current_license[:8]}****{current_license[-4:]}" if len(current_license) > 12 else current_license
                license_info['license_key'] = masked
                license_info['has_license'] = True
            else:
                license_info['license_key'] = ''
                license_info['has_license'] = False
            
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
                # Azure settings - only update non-empty fields
                azure_fields = ['azure_tenant_id', 'azure_subscription_id', 'azure_client_id', 'azure_client_secret']
                for field in azure_fields:
                    value = request.form.get(field, '').strip()
                    if value:  # Only update if value is provided
                        settings_data[field] = value
                success_message = 'Azure settings saved successfully!'
            
            elif section == 'slack':
                # Slack settings - handle checkbox separately
                if 'slack_enabled' in request.form.keys():
                    settings_data['slack_enabled'] = 'true' if request.form.get('slack_enabled') else 'false'
                
                # Only update non-empty fields
                slack_fields = ['slack_webhook_url', 'slack_channel', 'slack_cost_threshold']
                for field in slack_fields:
                    value = request.form.get(field, '').strip()
                    if value:  # Only update if value is provided
                        settings_data[field] = value
                success_message = 'Slack settings saved successfully!'
            
            elif section == 'email':
                # Email settings - handle checkbox separately
                if 'email_enabled' in request.form.keys():
                    settings_data['email_enabled'] = 'true' if request.form.get('email_enabled') else 'false'
                
                # Only update non-empty fields
                email_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email', 'email_recipients']
                for field in email_fields:
                    value = request.form.get(field, '').strip()
                    if value:  # Only update if value is provided
                        settings_data[field] = value
                success_message = 'Email settings saved successfully!'
            
            elif section == 'general':
                # General settings - only update fields that have values
                general_fields = ['log_level', 'session_timeout']
                for field in general_fields:
                    value = request.form.get(field, '').strip()
                    if value:  # Only add if not empty
                        settings_data[field] = value
                
                # Handle checkboxes - these always have a value (checked or not)
                if 'auto_analysis_enabled' in request.form.keys():
                    settings_data['auto_analysis_enabled'] = 'true' if request.form.get('auto_analysis_enabled') else 'false'
                
                # Handle auto analysis interval - only if provided
                auto_interval = request.form.get('auto_analysis_interval', '').strip()
                if auto_interval:
                    settings_data['auto_analysis_interval'] = auto_interval
                
                # Handle license key activation - ONLY if a non-empty key is provided
                license_key = request.form.get('license_key', '').strip()
                # Important: Skip license validation if field is empty or not changed
                if license_key and len(license_key) > 10:  # Minimum valid license key length
                    try:
                        # Save license key to environment and validate
                        import os
                        os.environ['KUBEOPT_LICENSE_KEY'] = license_key
                        
                        # Also save to .env file for persistence
                        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
                        updated_lines = []
                        license_found = False
                        
                        if os.path.exists(env_file):
                            with open(env_file, 'r') as f:
                                for line in f:
                                    if line.startswith('KUBEOPT_LICENSE_KEY=') or line.startswith('# KUBEOPT_LICENSE_KEY='):
                                        updated_lines.append(f'KUBEOPT_LICENSE_KEY={license_key}\n')
                                        license_found = True
                                    else:
                                        updated_lines.append(line)
                        
                        if not license_found:
                            updated_lines.append(f'\nKUBEOPT_LICENSE_KEY={license_key}\n')
                        
                        with open(env_file, 'w') as f:
                            f.writelines(updated_lines)
                        
                        # Validate the license
                        from infrastructure.services.license_validator import get_license_validator
                        validator = get_license_validator()
                        validator.license_key = license_key  # Update the instance
                        valid, info = validator.validate_license()
                        
                        if valid:
                            tier = info.get('tier', 'UNKNOWN')
                            success_message = f'License activated successfully! Tier: {tier}'
                            # Don't flash here - let it be done once at the end
                        else:
                            error_msg = info.get('error', 'Invalid license key')
                            success_message = f'General settings saved, but license validation failed: {error_msg}'
                    except Exception as e:
                        logger.error(f"Error activating license: {e}")
                        success_message = f'General settings saved, but license activation failed: {str(e)}'
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
                email_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email', 'email_recipients']
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
    
    @app.route('/get_settings', methods=['GET'])
    @auth_manager.require_auth
    def get_settings():
        """Get current settings"""
        try:
            settings = settings_manager.get_all_settings()
            # Don't send sensitive info like passwords
            safe_settings = {k: v for k, v in settings.items() if 'password' not in k.lower() and 'secret' not in k.lower()}
            return jsonify(safe_settings)
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return jsonify({'error': str(e)}), 500
    
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
            username = request.form.get('smtp_username', '').strip()
            password = request.form.get('smtp_password', '').strip()
            from_email = request.form.get('from_email', '').strip()
            email_recipients = request.form.get('email_recipients', '').strip()
            
            # Parse recipients from comma-separated string
            if email_recipients:
                recipients = [email.strip() for email in email_recipients.split(',') if email.strip()]
            else:
                recipients = [from_email or username] if (from_email or username) else []
            
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