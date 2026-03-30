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
import logging

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

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
        """Hash password using bcrypt."""
        if not BCRYPT_AVAILABLE:
            raise RuntimeError("bcrypt package is required. Install with: pip install bcrypt")
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
            if not BCRYPT_AVAILABLE:
                logger.error("Stored hash is bcrypt but bcrypt package not installed")
                return False
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        # TODO: migrate legacy SHA-256 hashes -- re-hash on next login
        logger.warning("Legacy SHA-256 hash detected. User must reset password.")
        return False

    def _upgrade_password_hash(self, username: str, password: str):
        """Auto-upgrade a legacy SHA-256 hash to bcrypt on successful login."""
        if not BCRYPT_AVAILABLE:
            return
        try:
            from infrastructure.services.settings_manager import settings_manager
            new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            settings_manager.save_settings({'user_password_hash': new_hash})
            logger.info(f"Upgraded password hash to bcrypt for user {username}")
        except Exception as e:
            logger.warning(f"Failed to upgrade password hash: {e}")
    
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
                return
            
            # Check if username exists in settings
            stored_username = settings_manager.get_setting('USER_USERNAME', '')
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
                logger.warning(f"Generated secure fallback credentials for user: {secure_username}")
                logger.warning("Set USER_USERNAME and USER_PASSWORD_HASH in .env for production!")
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
            stored_username = settings_manager.get_setting('USER_USERNAME', '')
            stored_password_hash = settings_manager.get_setting('USER_PASSWORD_HASH', '')
            
            # If no credentials available, authentication fails
            if not stored_username or not stored_password_hash:
                logger.error("No credentials configured! Set USER_USERNAME and USER_PASSWORD_HASH environment variables.")
                return False
            
            # Validate username
            if username != stored_username:
                return False

            # Validate password (supports bcrypt and legacy SHA-256)
            if self._verify_password(password, stored_password_hash):
                # Auto-upgrade legacy SHA-256 to bcrypt on successful login
                if not (stored_password_hash.startswith('$2b$') or stored_password_hash.startswith('$2a$')):
                    self._upgrade_password_hash(username, password)
                return True
            return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def create_session(self, username: str, remember: bool = False) -> str:
        """
        Create a new session for authenticated user.

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
            }

            self.active_sessions[session_token] = session_data
            return session_token

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return ""
    
    def validate_session(self, session_token: Optional[str] = None) -> bool:
        """Validate a session token."""
        try:
            if not session_token or session_token not in self.active_sessions:
                return False

            session_data = self.active_sessions[session_token]

            if datetime.now() - session_data['last_activity'] > self.session_timeout:
                self.destroy_session(session_token)
                return False

            session_data['last_activity'] = datetime.now()
            return True

        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False

    def destroy_session(self, session_token: Optional[str] = None):
        """Destroy a session."""
        try:
            if session_token and session_token in self.active_sessions:
                del self.active_sessions[session_token]
        except Exception as e:
            logger.error(f"Error destroying session: {e}")

    def get_current_user_by_token(self, session_token: str) -> Dict[str, Any]:
        """Get user info for a session token."""
        if session_token and session_token in self.active_sessions:
            return self.active_sessions[session_token]
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