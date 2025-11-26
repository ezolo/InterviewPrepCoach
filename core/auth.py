"""Authentication utilities (simple version for single-user mode)"""

import hashlib
from typing import Optional

def hash_password(password: str) -> str:
    """Hash a password using SHA-256
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash
    
    Args:
        password: Plain text password
        hashed: Hashed password
        
    Returns:
        True if password matches
    """
    return hash_password(password) == hashed

class SessionManager:
    """Simple session manager for single-user mode"""
    
    _current_user_id = None
    
    @classmethod
    def set_user(cls, user_id: int):
        """Set current user"""
        cls._current_user_id = user_id
    
    @classmethod
    def get_user_id(cls) -> int:
        """Get current user ID"""
        from config.settings import Settings
        return cls._current_user_id or Settings.DEFAULT_USER_ID
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if user is authenticated"""
        return cls._current_user_id is not None

