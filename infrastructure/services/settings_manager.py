#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
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
                if key.startswith(('AZURE_', 'SLACK_', 'EMAIL_', 'SMTP_', 'LOG_', 'PRODUCTION_', 'COST_', 'ANALYSIS_')):
                    config[key] = value
            
            self.config_cache = config
            logger.info(f"Settings loaded: {len(config)} configuration items")
            return config
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {}
    
    def save_settings(self, settings: Dict[str, str]) -> bool:
        """
        Save settings to .env file and environment
        
        Args:
            settings: Dictionary of settings to save
            
        Returns:
            bool: True if successful
        """
        try:
            # Create backup of current settings
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as src:
                    with open(self.backup_settings_file, 'w') as dst:
                        dst.write(src.read())
            
            # Prepare settings for writing
            config_lines = [
                "# AKS Cost Optimizer Configuration",
                f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "# Azure Configuration",
            ]
            
            # Group settings by category
            azure_settings = {k: v for k, v in settings.items() if k.startswith('AZURE_') or k in ['azure_tenant_id', 'azure_subscription_id', 'azure_client_id', 'azure_client_secret']}
            slack_settings = {k: v for k, v in settings.items() if k.startswith('SLACK_') or k in ['slack_enabled', 'slack_webhook_url', 'slack_channel', 'slack_cost_threshold']}
            email_settings = {k: v for k, v in settings.items() if k.startswith(('EMAIL_', 'SMTP_')) or k in ['email_enabled', 'email_username', 'email_password', 'email_recipients', 'smtp_server', 'smtp_port']}
            general_settings = {k: v for k, v in settings.items() if k in ['analysis_refresh_interval', 'cost_alert_threshold', 'log_level', 'production_mode']}
            
            # Write Azure settings
            for key, value in azure_settings.items():
                env_key = key.upper() if not key.startswith('AZURE_') else key
                if key in ['azure_tenant_id', 'azure_subscription_id', 'azure_client_id', 'azure_client_secret']:
                    env_key = f"AZURE_{key.split('_', 1)[1].upper()}"
                config_lines.append(f"{env_key}={value}")
            
            config_lines.extend(["", "# Slack Integration"])
            for key, value in slack_settings.items():
                env_key = key.upper() if not key.startswith('SLACK_') else key
                if key in ['slack_enabled', 'slack_webhook_url', 'slack_channel', 'slack_cost_threshold']:
                    env_key = f"SLACK_{key.split('_', 1)[1].upper()}" if '_' in key else 'SLACK_ENABLED'
                config_lines.append(f"{env_key}={value}")
            
            config_lines.extend(["", "# Email Settings"])
            for key, value in email_settings.items():
                env_key = key.upper()
                if key in ['email_enabled', 'email_username', 'email_password', 'email_recipients']:
                    env_key = f"EMAIL_{key.split('_', 1)[1].upper()}" if '_' in key else 'EMAIL_ENABLED'
                config_lines.append(f"{env_key}={value}")
            
            config_lines.extend(["", "# General Settings"])
            for key, value in general_settings.items():
                env_key = key.upper()
                if key == 'analysis_refresh_interval':
                    env_key = 'ANALYSIS_REFRESH_INTERVAL'
                elif key == 'cost_alert_threshold':
                    env_key = 'COST_ALERT_THRESHOLD'
                elif key == 'log_level':
                    env_key = 'LOG_LEVEL'
                elif key == 'production_mode':
                    env_key = 'PRODUCTION_MODE'
                config_lines.append(f"{env_key}={value}")
            
            # Handle custom environment variables
            if 'custom_env_vars' in settings and settings['custom_env_vars']:
                config_lines.extend(["", "# Custom Environment Variables"])
                for line in settings['custom_env_vars'].split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        config_lines.append(line)
            
            # Write to .env file
            with open(self.settings_file, 'w') as f:
                f.write('\n'.join(config_lines))
            
            # Update environment variables for current session
            for key, value in settings.items():
                env_key = self._get_env_key(key)
                os.environ[env_key] = str(value)
            
            # Reload settings cache
            self.load_settings()
            
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
            'slack_cost_threshold': 'SLACK_COST_THRESHOLD',
            'email_enabled': 'EMAIL_ENABLED',
            'smtp_server': 'SMTP_SERVER',
            'smtp_port': 'SMTP_PORT',
            'email_username': 'EMAIL_USERNAME',
            'email_password': 'EMAIL_PASSWORD',
            'email_recipients': 'EMAIL_RECIPIENTS',
            'analysis_refresh_interval': 'ANALYSIS_REFRESH_INTERVAL',
            'cost_alert_threshold': 'COST_ALERT_THRESHOLD',
            'log_level': 'LOG_LEVEL',
            'production_mode': 'PRODUCTION_MODE'
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
                <p><em>Powered by KubeVista & Nivaya Technologies</em></p>
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
                    <p><em>AKS Cost Optimizer by KubeVista & Nivaya Technologies</em></p>
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