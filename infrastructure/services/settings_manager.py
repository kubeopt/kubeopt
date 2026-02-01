#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Settings Manager for AKS Cost Optimizer
=======================================

Manages application configuration, environment variables, and settings persistence.
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Multi-Environment Settings Manager
    ==================================
    
    Supports three deployment scenarios:
    1. Local Development: .env file in current directory
    2. Docker/Self-Hosted: Volume mount at /app/config or SETTINGS_PATH
    3. Railway: GraphQL API sync + volume storage
    """
    
    def __init__(self):
        self.config_cache = {}
        self.deployment_type = self._detect_deployment_type()
        self.settings_file, self.backup_settings_file = self._get_settings_paths()
        
        # Railway API configuration (only used in Railway environment)
        self.railway_config = self._setup_railway_config()
        
        logger.info(f"🔧 Settings Manager initialized for: {self.deployment_type}")
        self.load_settings()
    
    def _detect_deployment_type(self) -> str:
        """Detect which deployment environment we're running in"""
        if os.getenv('RAILWAY_ENVIRONMENT'):
            return 'railway'
        elif os.path.exists('/app/config') and os.access('/app/config', os.W_OK):
            return 'docker_volume'
        elif os.getenv('SETTINGS_PATH'):
            return 'custom_path'
        else:
            return 'local'
    
    def _get_settings_paths(self) -> tuple:
        """Get appropriate settings file paths based on deployment type"""
        if self.deployment_type == 'railway':
            # Railway: Use volume if available, fall back to app directory
            if os.getenv('RAILWAY_VOLUME_MOUNT_PATH'):
                settings_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
                logger.info(f"🚂 Railway volume detected: {settings_dir}")
            else:
                settings_dir = '/app'
                logger.info("🚂 Railway environment without volume")
        elif self.deployment_type == 'docker_volume':
            settings_dir = '/app/config'
            logger.info(f"🐳 Docker volume mount detected: {settings_dir}")
        elif self.deployment_type == 'custom_path':
            settings_dir = os.getenv('SETTINGS_PATH')
            logger.info(f"📁 Custom settings path: {settings_dir}")
        else:
            settings_dir = os.getcwd()
            logger.info(f"💻 Local development: {settings_dir}")
        
        # Ensure directory exists
        os.makedirs(settings_dir, exist_ok=True)
        
        settings_file = os.path.join(settings_dir, '.env')
        backup_file = os.path.join(settings_dir, '.env.backup')
        
        return settings_file, backup_file
    
    def _setup_railway_config(self) -> dict:
        """Setup Railway API configuration if in Railway environment"""
        if self.deployment_type != 'railway':
            return {}
        
        return {
            'api_token': os.getenv('RAILWAY_API_TOKEN'),
            'project_id': os.getenv('RAILWAY_PROJECT_ID'),
            'environment_id': os.getenv('RAILWAY_ENVIRONMENT_ID'),
            'service_id': os.getenv('RAILWAY_SERVICE_ID'),
            'api_url': 'https://backboard.railway.com/graphql/v2'
        }
    
    def load_settings(self) -> Dict[str, str]:
        """
        Load settings with priority: Volume/File Settings > Environment Variables > Defaults
        
        Returns:
            Dict of current configuration
        """
        try:
            config = {}
            
            # 1. Start with environment variables (defaults in Railway, all vars locally)
            for key, value in os.environ.items():
                if key.startswith(('AZURE_', 'SLACK_', 'EMAIL_', 'SMTP_', 'LOG_', 'PRODUCTION_', 'COST_', 'ANALYSIS_', 'AUTO_', 'DATABASE_', 'USER_', 'KUBEOPT_')):
                    config[key] = value
            
            # 2. Override with settings file (customer overrides)
            if os.path.exists(self.settings_file):
                logger.info(f"📄 Loading settings file: {self.settings_file}")
                with open(self.settings_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            config[key] = value
                            logger.debug(f"  Loaded: {key}")
            else:
                logger.info(f"📄 No settings file found at: {self.settings_file}")
            
            self.config_cache = config
            logger.info(f"✅ Settings loaded ({self.deployment_type}): {len(config)} items")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error loading settings: {e}")
            return {}
    
    def save_settings(self, new_settings: Dict[str, str]) -> bool:
        """
        Multi-Environment Settings Save
        ===============================
        
        Saves settings based on deployment type:
        - Local: Saves to .env file
        - Docker: Saves to volume mount
        - Railway: Saves to file AND syncs to Railway API
        
        Args:
            new_settings: Dictionary of new settings to save
            
        Returns:
            bool: True if successful
        """
        try:
            # Create backup of current settings
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as src:
                    with open(self.backup_settings_file, 'w') as dst:
                        dst.write(src.read())
            
            # Load existing settings first
            existing_settings = self.load_settings()
            
            # Convert form field names to environment variable names and merge
            merged_settings = existing_settings.copy()
            for key, value in new_settings.items():
                env_key = self._get_env_key(key)
                merged_settings[env_key] = str(value)
                # Also update current environment
                os.environ[env_key] = str(value)
            
            # Group merged settings by category for organized output
            azure_settings = {k: v for k, v in merged_settings.items() if k.startswith('AZURE_')}
            slack_settings = {k: v for k, v in merged_settings.items() if k.startswith('SLACK_') or k == 'APP_URL'}
            email_settings = {k: v for k, v in merged_settings.items() if k.startswith(('EMAIL_', 'SMTP_', 'FROM_'))}
            general_settings = {k: v for k, v in merged_settings.items() if k in [
                'ANALYSIS_REFRESH_INTERVAL', 'COST_ALERT_THRESHOLD', 'LOG_LEVEL', 
                'PRODUCTION_MODE', 'AUTO_ANALYSIS_ENABLED', 'AUTO_ANALYSIS_INTERVAL',
                'COST_CACHE_HOURS'
            ]}
            database_settings = {k: v for k, v in merged_settings.items() if k.startswith('DATABASE_')}
            
            # Handle custom environment variables
            custom_env_vars = merged_settings.get('CUSTOM_ENV_VARS', '')
            
            # Build output lines
            config_lines = [
                "# AKS Cost Optimizer Configuration",
                f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "# Azure Configuration"
            ]
            
            # Write Azure settings
            for key, value in sorted(azure_settings.items()):
                config_lines.append(f"{key}={value}")
            
            # Write Slack settings
            if slack_settings is not None and slack_settings:
                config_lines.extend(["", "# Slack Integration"])
                for key, value in sorted(slack_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write Email settings
            if email_settings is not None and email_settings:
                config_lines.extend(["", "# Email Settings"])
                for key, value in sorted(email_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write General settings
            if general_settings is not None and general_settings:
                config_lines.extend(["", "# General Settings"])
                for key, value in sorted(general_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write Database settings
            if database_settings is not None and database_settings:
                config_lines.extend(["", "# Database Cleanup Settings"])
                for key, value in sorted(database_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write any other settings not categorized above
            other_settings = {k: v for k, v in merged_settings.items() 
                            if not k.startswith(('AZURE_', 'SLACK_', 'EMAIL_', 'SMTP_', 'FROM_', 'DATABASE_')) 
                            and k not in ['APP_URL', 'ANALYSIS_REFRESH_INTERVAL', 'COST_ALERT_THRESHOLD', 
                                        'LOG_LEVEL', 'PRODUCTION_MODE', 'AUTO_ANALYSIS_ENABLED', 
                                        'AUTO_ANALYSIS_INTERVAL', 'COST_CACHE_HOURS', 'CUSTOM_ENV_VARS']}
            
            if other_settings is not None and other_settings:
                config_lines.extend(["", "# Other Settings"])
                for key, value in sorted(other_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Handle custom environment variables
            if custom_env_vars is not None and custom_env_vars:
                config_lines.extend(["", "# Custom Environment Variables"])
                for line in custom_env_vars.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        config_lines.append(line)
            
            # Write to .env file
            with open(self.settings_file, 'w') as f:
                f.write('\n'.join(config_lines))
            
            # Reload settings cache
            self.config_cache = merged_settings
            
            # Railway-specific: Sync to Railway API if in Railway environment
            if hasattr(self, 'deployment_type') and self.deployment_type == 'railway' and hasattr(self, '_can_sync_to_railway') and self._can_sync_to_railway():
                railway_success = self._sync_to_railway_api(new_settings)
                if railway_success:
                    logger.info("🚂 Settings synced to Railway API")
                else:
                    logger.warning("⚠️ Railway API sync failed, but local file saved")
            
            # Check if auto-analysis setting changed and restart scheduler if needed
            if 'auto_analysis_enabled' in new_settings:
                try:
                    from infrastructure.services.auto_analysis_scheduler import auto_scheduler
                    logger.info("🔄 Auto-analysis setting changed, restarting scheduler...")
                    auto_scheduler.restart_scheduler()
                except Exception as e:
                    logger.warning(f"⚠️ Could not restart auto-analysis scheduler: {e}")
            
            logger.info(f"✅ Settings saved successfully ({getattr(self, 'deployment_type', 'standard')} mode)")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def _get_env_key(self, setting_key: str) -> str:
        """
        Convert setting key to environment variable key
        
        Args:
            setting_key: Setting key from form
            
        Returns:
            str: Environment variable key
        """
        mapping = {
            'azure_tenant_id': 'AZURE_TENANT_ID',
            'azure_subscription_id': 'AZURE_SUBSCRIPTION_ID',
            'azure_client_id': 'AZURE_CLIENT_ID',
            'azure_client_secret': 'AZURE_CLIENT_SECRET',
            'slack_enabled': 'SLACK_ENABLED',
            'slack_webhook_url': 'SLACK_WEBHOOK_URL',
            'slack_channel': 'SLACK_CHANNEL',
            'app_url': 'APP_URL',
            'email_enabled': 'EMAIL_ENABLED',
            'smtp_server': 'SMTP_SERVER',
            'smtp_port': 'SMTP_PORT',
            'smtp_username': 'SMTP_USERNAME',
            'smtp_password': 'SMTP_PASSWORD',
            'from_email': 'FROM_EMAIL',
            'email_recipients': 'EMAIL_RECIPIENTS',
            'analysis_refresh_interval': 'ANALYSIS_REFRESH_INTERVAL',
            'cost_alert_threshold': 'COST_ALERT_THRESHOLD',
            'log_level': 'LOG_LEVEL',
            'production_mode': 'PRODUCTION_MODE',
            'auto_analysis_enabled': 'AUTO_ANALYSIS_ENABLED',
            'auto_analysis_interval': 'AUTO_ANALYSIS_INTERVAL',
            'database_cleanup_enabled': 'DATABASE_CLEANUP_ENABLED',
            'database_retention_days': 'DATABASE_RETENTION_DAYS',
            'database_cleanup_interval_hours': 'DATABASE_CLEANUP_INTERVAL_HOURS',
            'cost_cache_hours': 'COST_CACHE_HOURS'
        }
        
        return mapping.get(setting_key, setting_key.upper())
    
    def get_settings(self) -> Dict[str, str]:
        """
        Get current settings
        
        Returns:
            Dict of current settings
        """
        if not self.config_cache:
            self.load_settings()
        return self.config_cache.copy()
    
    def get_all_settings(self) -> Dict[str, str]:
        """
        Get all current settings (alias for get_settings)
        
        Returns:
            Dict of current settings
        """
        return self.get_settings()
    
    def get_setting(self, key: str, default: str = '') -> str:
        """
        Get individual setting value
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            str: Setting value
        """
        config = self.get_settings()
        return config.get(key, default)
    
    def update_setting(self, key: str, value: str) -> None:
        """
        Update a single setting value in memory (call save_settings to persist)
        
        Args:
            key: Setting key (will be converted to uppercase)
            value: Setting value
        """
        if not self.config_cache:
            self.load_settings()
        
        # Convert key to uppercase for .env format
        env_key = key.upper() if not key.isupper() else key
        
        # Update the cache with lowercase key for consistency
        self.config_cache[env_key.lower()] = value
        
        # Also set in environment for immediate use
        os.environ[env_key] = str(value)
        
        logger.info(f"Updated setting {env_key} in memory")
    
    def test_slack_integration(self) -> Dict[str, Any]:
        """
        Test Slack webhook integration
        
        Returns:
            Dict with test results
        """
        try:
            webhook_url = self.get_setting('SLACK_WEBHOOK_URL')
            channel = self.get_setting('SLACK_CHANNEL', '#general')
            
            if not webhook_url:
                return {'success': False, 'message': 'Slack webhook URL not configured'}
            
            message = {
                'channel': channel,
                'username': 'AKS Cost Optimizer',
                'text': f'🧪 Test message from AKS Cost Optimizer - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'icon_emoji': ':cloud:'
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            
            if response.status_code == 200:
                logger.info("Slack test message sent successfully")
                return {'success': True, 'message': 'Test message sent to Slack'}
            else:
                logger.error(f"Slack test failed: {response.status_code} - {response.text}")
                return {'success': False, 'message': f'Slack API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error testing Slack integration: {e}")
            return {'success': False, 'message': str(e)}
    
    def test_slack_integration_with_values(self, webhook_url: str, channel: str = '#general') -> Dict[str, Any]:
        """
        Test Slack webhook integration with provided values (allows testing before saving)
        
        Args:
            webhook_url: Slack webhook URL to test
            channel: Slack channel for the test message
        
        Returns:
            Dict with test results
        """
        try:
            if not webhook_url:
                return {'success': False, 'message': 'Slack webhook URL not provided'}
            
            message = {
                'channel': channel,
                'username': 'AKS Cost Optimizer',
                'text': f'🧪 Test message from AKS Cost Optimizer - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'icon_emoji': ':cloud:'
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            
            if response.status_code == 200:
                logger.info("Slack test message sent successfully with provided values")
                return {'success': True, 'message': 'Test message sent to Slack successfully!'}
            else:
                logger.error(f"Slack test failed: {response.status_code} - {response.text}")
                return {'success': False, 'message': f'Slack API error: {response.status_code} - {response.text}'}
                
        except Exception as e:
            logger.error(f"Error testing Slack integration with provided values: {e}")
            return {'success': False, 'message': str(e)}
    
    def test_email_configuration(self, smtp_server: str, smtp_port: int, username: str, password: str, recipients: List[str]) -> Dict[str, Any]:
        """
        Test email configuration
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            username: Email username
            password: Email password
            recipients: List of recipient emails
            
        Returns:
            Dict with test results
        """
        try:
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = 'AKS Cost Optimizer - Test Email'
            
            body = f"""
            <html>
            <body>
                <h2>AKS Cost Optimizer Test Email</h2>
                <p>This is a test email from your AKS Cost Optimizer instance.</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Server:</strong> {smtp_server}:{smtp_port}</p>
                <p>If you received this email, your email configuration is working correctly!</p>
                <hr>
                <p><em>Powered by kubeopt & Nivaya Technologies</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(username, recipients, text)
            server.quit()
            
            logger.info(f"Test email sent successfully to {len(recipients)} recipients")
            return {'success': True, 'message': f'Test email sent to {len(recipients)} recipients'}
            
        except Exception as e:
            logger.error(f"Error testing email configuration: {e}")
            return {'success': False, 'message': str(e)}
    
    def send_cost_alert(self, cluster_name: str, cost_data: Dict[str, Any]):
        """
        Send cost alert via configured channels
        
        Args:
            cluster_name: Name of the cluster
            cost_data: Cost analysis data
        """
        try:
            current_cost = cost_data.get('total_cost', 0)
            threshold = float(self.get_setting('COST_ALERT_THRESHOLD', '500'))
            
            if current_cost > threshold:
                # Send Slack alert if enabled
                if self.get_setting('SLACK_ENABLED', 'false').lower() == 'true':
                    self._send_slack_alert(cluster_name, cost_data)
                
                # Send email alert if enabled
                if self.get_setting('EMAIL_ENABLED', 'false').lower() == 'true':
                    self._send_email_alert(cluster_name, cost_data)
                    
        except Exception as e:
            logger.error(f"Error sending cost alert: {e}")
    
    def _send_slack_alert(self, cluster_name: str, cost_data: Dict[str, Any]):
        """Send Slack cost alert"""
        try:
            webhook_url = self.get_setting('SLACK_WEBHOOK_URL')
            channel = self.get_setting('SLACK_CHANNEL', '#general')
            
            if webhook_url is not None and webhook_url:
                current_cost = cost_data.get('total_cost', 0)
                threshold = float(self.get_setting('COST_ALERT_THRESHOLD', '500'))
                
                message = {
                    'channel': channel,
                    'username': 'AKS Cost Optimizer',
                    'text': f'🚨 Cost Alert for {cluster_name}',
                    'attachments': [{
                        'color': 'danger',
                        'fields': [
                            {'title': 'Cluster', 'value': cluster_name, 'short': True},
                            {'title': 'Current Cost', 'value': f'${current_cost:.2f}', 'short': True},
                            {'title': 'Threshold', 'value': f'${threshold:.2f}', 'short': True},
                            {'title': 'Overage', 'value': f'${current_cost - threshold:.2f}', 'short': True}
                        ]
                    }],
                    'icon_emoji': ':warning:'
                }
                
                requests.post(webhook_url, json=message, timeout=10)
                logger.info(f"Slack cost alert sent for {cluster_name}")
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _send_email_alert(self, cluster_name: str, cost_data: Dict[str, Any]):
        """Send email cost alert"""
        try:
            smtp_server = self.get_setting('SMTP_SERVER')
            smtp_port = int(self.get_setting('SMTP_PORT', '587'))
            username = self.get_setting('EMAIL_USERNAME')
            password = self.get_setting('EMAIL_PASSWORD')
            recipients = self.get_setting('EMAIL_RECIPIENTS', '').split(',')
            recipients = [email.strip() for email in recipients if email.strip()]
            
            if smtp_server and username and password and recipients:
                current_cost = cost_data.get('total_cost', 0)
                threshold = float(self.get_setting('COST_ALERT_THRESHOLD', '500'))
                
                msg = MIMEMultipart()
                msg['From'] = username
                msg['To'] = ', '.join(recipients)
                msg['Subject'] = f'AKS Cost Alert - {cluster_name} (${current_cost:.2f})'
                
                body = f"""
                <html>
                <body>
                    <h2>🚨 AKS Cost Alert</h2>
                    <p>The cluster <strong>{cluster_name}</strong> has exceeded the cost threshold.</p>
                    <table border="1" cellpadding="5" cellspacing="0">
                        <tr><td><strong>Cluster Name</strong></td><td>{cluster_name}</td></tr>
                        <tr><td><strong>Current Cost</strong></td><td>${current_cost:.2f}</td></tr>
                        <tr><td><strong>Alert Threshold</strong></td><td>${threshold:.2f}</td></tr>
                        <tr><td><strong>Overage</strong></td><td>${current_cost - threshold:.2f}</td></tr>
                        <tr><td><strong>Timestamp</strong></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    </table>
                    <p>Please review your cluster resources and consider optimization recommendations.</p>
                    <hr>
                    <p><em>AKS Cost Optimizer by kubeopt & Nivaya Technologies</em></p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(username, password)
                server.sendmail(username, recipients, msg.as_string())
                server.quit()
                
                logger.info(f"Email cost alert sent for {cluster_name}")
                
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def get_custom_env_vars(self) -> str:
        """
        Get custom environment variables as text
        
        Returns:
            str: Custom environment variables
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    content = f.read()
                    
                # Extract custom variables (after "# Custom Environment Variables")
                if "# Custom Environment Variables" in content:
                    custom_section = content.split("# Custom Environment Variables")[1]
                    return custom_section.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting custom env vars: {e}")
            return ""

    def _can_sync_to_railway(self) -> bool:
        """Check if Railway API sync is possible"""
        if not hasattr(self, 'railway_config'):
            return False
        required_keys = ['api_token', 'project_id', 'environment_id']
        return all(self.railway_config.get(key) for key in required_keys)
    
    def _sync_to_railway_api(self, settings: Dict[str, str]) -> bool:
        """Sync settings to Railway API using GraphQL"""
        try:
            if not self._can_sync_to_railway():
                logger.warning("🚂 Railway API sync skipped: missing configuration")
                return False
            
            # Prepare GraphQL mutation for multiple variables
            variables_input = []
            for key, value in settings.items():
                env_key = self._get_env_key(key)
                variables_input.append({
                    "name": env_key,
                    "value": str(value)
                })
            
            mutation = """
            mutation variableCollectionUpsert($input: VariableCollectionUpsertInput!) {
                variableCollectionUpsert(input: $input)
            }
            """
            
            variables = {
                "input": {
                    "projectId": self.railway_config['project_id'],
                    "environmentId": self.railway_config['environment_id'],
                    "variables": variables_input,
                    "skipDeploys": True  # Don't redeploy for settings changes
                }
            }
            
            # Add serviceId if available (for service-specific variables)
            if self.railway_config.get('service_id'):
                variables["input"]["serviceId"] = self.railway_config['service_id']
            
            # Make GraphQL request
            headers = {
                'Authorization': f'Bearer {self.railway_config["api_token"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'query': mutation,
                'variables': variables
            }
            
            logger.debug("🚂 Syncing to Railway API...")
            response = requests.post(
                self.railway_config['api_url'],
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'errors' in result:
                    logger.error(f"🚂 Railway API errors: {result['errors']}")
                    return False
                else:
                    logger.info(f"🚂 Successfully synced {len(settings)} settings to Railway")
                    return True
            else:
                logger.error(f"🚂 Railway API request failed: {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Railway API sync error: {e}")
            return False
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment type and configuration info for debugging"""
        info = {
            'deployment_type': getattr(self, 'deployment_type', 'unknown'),
            'settings_file': getattr(self, 'settings_file', 'unknown'),
            'can_write_files': os.access(os.path.dirname(getattr(self, 'settings_file', '.')), os.W_OK) if hasattr(self, 'settings_file') else False
        }
        
        if hasattr(self, 'deployment_type') and self.deployment_type == 'railway':
            info['railway_api_available'] = self._can_sync_to_railway()
            info['railway_volume'] = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
            info['railway_environment'] = os.getenv('RAILWAY_ENVIRONMENT')
        
        return info

# Global settings manager instance
settings_manager = SettingsManager()