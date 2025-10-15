#!/usr/bin/env python3
"""
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
    Centralized settings and configuration management
    """
    
    def __init__(self):
        self.settings_file = os.path.join(os.getcwd(), '.env')
        self.backup_settings_file = os.path.join(os.getcwd(), '.env.backup')
        self.config_cache = {}
        self.load_settings()
    
    def load_settings(self) -> Dict[str, str]:
        """
        Load settings from environment and .env file
        
        Returns:
            Dict of current configuration
        """
        try:
            config = {}
            
            # Load from .env file if it exists
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"\'')
            
            # Override with actual environment variables
            for key, value in os.environ.items():
                if key.startswith(('AZURE_', 'SLACK_', 'EMAIL_', 'SMTP_', 'LOG_', 'PRODUCTION_', 'COST_', 'ANALYSIS_', 'AUTO_')):
                    config[key] = value
            
            self.config_cache = config
            logger.info(f"Settings loaded: {len(config)} configuration items")
            return config
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {}
    
    def save_settings(self, new_settings: Dict[str, str]) -> bool:
        """
        Save settings to .env file and environment - MERGES with existing settings
        
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
                'PRODUCTION_MODE', 'AUTO_ANALYSIS_ENABLED', 'AUTO_ANALYSIS_INTERVAL'
            ]}
            
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
            if slack_settings:
                config_lines.extend(["", "# Slack Integration"])
                for key, value in sorted(slack_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write Email settings
            if email_settings:
                config_lines.extend(["", "# Email Settings"])
                for key, value in sorted(email_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write General settings
            if general_settings:
                config_lines.extend(["", "# General Settings"])
                for key, value in sorted(general_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Write any other settings not categorized above
            other_settings = {k: v for k, v in merged_settings.items() 
                            if not k.startswith(('AZURE_', 'SLACK_', 'EMAIL_', 'SMTP_', 'FROM_')) 
                            and k not in ['APP_URL', 'ANALYSIS_REFRESH_INTERVAL', 'COST_ALERT_THRESHOLD', 
                                        'LOG_LEVEL', 'PRODUCTION_MODE', 'AUTO_ANALYSIS_ENABLED', 
                                        'AUTO_ANALYSIS_INTERVAL', 'CUSTOM_ENV_VARS']}
            
            if other_settings:
                config_lines.extend(["", "# Other Settings"])
                for key, value in sorted(other_settings.items()):
                    config_lines.append(f"{key}={value}")
            
            # Handle custom environment variables
            if custom_env_vars:
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
            
            # Check if auto-analysis setting changed and restart scheduler if needed
            if 'auto_analysis_enabled' in new_settings:
                try:
                    from infrastructure.services.auto_analysis_scheduler import auto_scheduler
                    logger.info("🔄 Auto-analysis setting changed, restarting scheduler...")
                    auto_scheduler.restart_scheduler()
                except Exception as e:
                    logger.warning(f"⚠️ Could not restart auto-analysis scheduler: {e}")
            
            logger.info("Settings saved successfully")
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
            'auto_analysis_interval': 'AUTO_ANALYSIS_INTERVAL'
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
            
            if webhook_url:
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

# Global settings manager instance
settings_manager = SettingsManager()