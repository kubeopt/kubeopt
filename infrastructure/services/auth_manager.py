#!/usr/bin/env python3
"""
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
        self.default_users = {
            'kubeopt': {
                'password_hash': self._hash_password('kubeopt'),
                'role': 'admin',
                'created': datetime.now()
            }
        }
        self.active_sessions = {}
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = b'kubeopt_aks_optimizer_2024'  # Static salt for simplicity
        return hashlib.sha256(salt + password.encode()).hexdigest()
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate user credentials
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            bool: True if authentication successful
        """
        try:
            if username not in self.default_users:
                logger.warning(f"Authentication attempt for non-existent user: {username}")
                return False
            
            user = self.default_users[username]
            password_hash = self._hash_password(password)
            
            if password_hash == user['password_hash']:
                logger.info(f"Successful authentication for user: {username}")
                return True
            else:
                logger.warning(f"Failed authentication for user: {username}")
                return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def create_session(self, username: str) -> str:
        """
        Create a new session for authenticated user
        
        Args:
            username: Authenticated username
            
        Returns:
            str: Session token
        """
        try:
            session_token = secrets.token_urlsafe(32)
            session_data = {
                'username': username,
                'role': self.default_users[username]['role'],
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
                from flask import redirect, url_for, flash
                flash('Please log in to access this page', 'error')
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