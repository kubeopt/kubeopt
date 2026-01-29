#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Authentication Manager for AKS Cost Optimizer
=============================================

Provides secure authentication and session management for the web interface.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import session, request
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Authentication manager with secure session handling
    """
    
    def __init__(self):
        self.session_timeout = timedelta(hours=8)  # 8-hour session timeout
        self.active_sessions = {}
        
        # Initialize default credentials in settings if not exists
        self._ensure_default_credentials()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = b'kubeopt_aks_optimizer_2024'  # Static salt for simplicity
        return hashlib.sha256(salt + password.encode()).hexdigest()
    
    def _ensure_default_credentials(self):
        """Initialize credentials from environment variables or settings"""
        try:
            from infrastructure.services.settings_manager import settings_manager
            
            # Check environment variables first (Railway deployment)
            env_username = os.getenv('USER_USERNAME', '')
            env_password_hash = os.getenv('USER_PASSWORD_HASH', '')
            env_role = os.getenv('USER_ROLE', 'admin')
            
            if env_username and env_password_hash:
                # Use environment variables (Production/Railway)
                env_settings = {
                    'user_username': env_username,
                    'user_password_hash': env_password_hash,
                    'user_role': env_role
                }
                settings_manager.save_settings(env_settings)
                logger.info(f"🔧 Initialized credentials from environment: {env_username}")
                return
            
            # Check if username exists in settings
            stored_username = settings_manager.get_setting('user_username', '')
            if not stored_username:
                # Fallback to secure default (NOT kubeopt/kubeopt)
                import secrets
                secure_username = f"admin_{secrets.token_hex(3)}"
                secure_password = secrets.token_urlsafe(12)
                
                default_settings = {
                    'user_username': secure_username,
                    'user_password_hash': self._hash_password(secure_password),
                    'user_role': 'admin'
                }
                settings_manager.save_settings(default_settings)
                logger.warning(f"🔧 Generated secure fallback credentials: {secure_username} / {secure_password}")
                logger.warning("⚠️  SAVE THESE CREDENTIALS! Set USER_USERNAME and USER_PASSWORD_HASH in production!")
        except Exception as e:
            logger.error(f"Failed to initialize credentials: {e}")
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate user credentials using persistent settings
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            bool: True if authentication successful
        """
        try:
            from infrastructure.services.settings_manager import settings_manager
            
            # Get stored credentials (no fallback defaults)
            stored_username = settings_manager.get_setting('user_username', '')
            stored_password_hash = settings_manager.get_setting('user_password_hash', '')
            
            # If no credentials available, authentication fails
            if not stored_username or not stored_password_hash:
                logger.error("❌ No credentials configured! Set USER_USERNAME and USER_PASSWORD_HASH environment variables.")
                return False
            
            # Validate username
            if username != stored_username:
                logger.warning(f"Authentication attempt for non-existent user: {username}")
                return False
            
            # Validate password
            password_hash = self._hash_password(password)
            if password_hash == stored_password_hash:
                logger.info(f"Successful authentication for user: {username}")
                return True
            else:
                logger.warning(f"Failed authentication for user: {username}")
                return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def create_session(self, username: str, remember: bool = False) -> str:
        """
        Create a new session for authenticated user
        
        Args:
            username: Authenticated username
            remember: Whether to create a long-lived session
            
        Returns:
            str: Session token
        """
        try:
            from infrastructure.services.settings_manager import settings_manager
            
            session_token = secrets.token_urlsafe(32)
            user_role = settings_manager.get_setting('user_role', 'admin')
            
            session_data = {
                'username': username,
                'role': user_role,
                'created': datetime.now(),
                'last_activity': datetime.now(),
                'ip_address': request.remote_addr if request else 'unknown'
            }
            
            self.active_sessions[session_token] = session_data
            
            # Store in Flask session
            session['authenticated'] = True
            session['username'] = username
            session['role'] = session_data['role']
            session['session_token'] = session_token
            
            logger.info(f"Session created for user: {username}")
            return session_token
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return ""
    
    def validate_session(self, session_token: Optional[str] = None) -> bool:
        """
        Validate current session
        
        Args:
            session_token: Optional session token to validate
            
        Returns:
            bool: True if session is valid
        """
        try:
            # Use provided token or get from session
            token = session_token or session.get('session_token')
            
            if not token or token not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[token]
            
            # Check session timeout
            if datetime.now() - session_data['last_activity'] > self.session_timeout:
                self.destroy_session(token)
                return False
            
            # Update last activity
            session_data['last_activity'] = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def destroy_session(self, session_token: Optional[str] = None):
        """
        Destroy session
        
        Args:
            session_token: Optional session token to destroy
        """
        try:
            # Use provided token or get from session
            token = session_token or session.get('session_token')
            
            if token and token in self.active_sessions:
                username = self.active_sessions[token]['username']
                del self.active_sessions[token]
                logger.info(f"Session destroyed for user: {username}")
            
            # Clear Flask session
            session.clear()
            
        except Exception as e:
            logger.error(f"Error destroying session: {e}")
    
    def require_auth(self, f):
        """
        Decorator to require authentication for routes
        """
        def wrapper(*args, **kwargs):
            if not self.validate_session():
                from flask import redirect, url_for
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user info
        
        Returns:
            Dict containing user information
        """
        try:
            session_token = session.get('session_token')
            if session_token and session_token in self.active_sessions:
                return self.active_sessions[session_token]
            return {}
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return {}
    
    def cleanup_expired_sessions(self):
        """
        Clean up expired sessions
        """
        try:
            current_time = datetime.now()
            expired_tokens = []
            
            for token, session_data in self.active_sessions.items():
                if current_time - session_data['last_activity'] > self.session_timeout:
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                username = self.active_sessions[token]['username']
                del self.active_sessions[token]
                logger.info(f"Expired session cleaned up for user: {username}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions
        
        Returns:
            int: Number of active sessions
        """
        return len(self.active_sessions)
    
    def is_admin(self) -> bool:
        """
        Check if current user is admin
        
        Returns:
            bool: True if current user is admin
        """
        user = self.get_current_user()
        return user.get('role') == 'admin'

# Global authentication manager instance
auth_manager = AuthManager()