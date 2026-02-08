"""
Security utilities for Everest Inventory System
- Password hashing and verification
- Session management
- Authentication helpers
"""

import os
import hashlib
import time
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security constants
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 30 minutes default
SALT = os.getenv("PASSWORD_SALT", "everest_inventory_salt_2026")  # Default salt


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hexadecimal hash string
    """
    salted = f"{password}{SALT}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(input_password: str, stored_hash: Optional[str] = None) -> bool:
    """
    Verify password against stored hash or environment variable.
    
    Args:
        input_password: Password entered by user
        stored_hash: Optional pre-computed hash. If None, uses env var.
        
    Returns:
        True if password matches, False otherwise
    """
    # Get stored password from env
    env_password = os.getenv("MANAGER_PASSWORD")
    
    if not env_password:
        # Fallback to hardcoded for backward compatibility (REMOVE IN PRODUCTION)
        import streamlit as st
        st.warning("⚠️ Using fallback password. Please set MANAGER_PASSWORD in .env file!")
        return input_password == "1234"
    
    # Compare hashes
    if stored_hash:
        return hash_password(input_password) == stored_hash
    else:
        # Hash env password and compare
        return hash_password(input_password) == hash_password(env_password)


def check_session_timeout(session_state) -> Tuple[bool, str]:
    """
    Check if session has timed out.
    
    Args:
        session_state: Streamlit session_state object
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Initialize last activity if not exists
    if "last_activity" not in session_state:
        session_state.last_activity = time.time()
        return True, "Session initialized"
    
    # Check if logged in
    if not session_state.get("logged_in", False):
        return True, "Not logged in"
    
    # Calculate elapsed time
    elapsed = time.time() - session_state.last_activity
    
    if elapsed > SESSION_TIMEOUT:
        # Session expired
        session_state.logged_in = False
        return False, f"Session expired after {SESSION_TIMEOUT//60} minutes of inactivity"
    
    # Update activity timestamp
    session_state.last_activity = time.time()
    return True, "Session active"


def get_session_remaining_time(session_state) -> int:
    """
    Get remaining session time in seconds.
    
    Args:
        session_state: Streamlit session_state object
        
    Returns:
        Remaining time in seconds
    """
    if "last_activity" not in session_state:
        return SESSION_TIMEOUT
    
    elapsed = time.time() - session_state.last_activity
    remaining = SESSION_TIMEOUT - elapsed
    return max(0, int(remaining))


def format_session_time(seconds: int) -> str:
    """
    Format session time for display.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string (e.g., "25분 30초")
    """
    if seconds <= 0:
        return "만료됨"
    
    minutes = seconds // 60
    secs = seconds % 60
    
    if minutes > 0:
        return f"{minutes}분 {secs}초"
    else:
        return f"{secs}초"


# For testing
if __name__ == "__main__":
    # Test password hashing
    test_pwd = "test123"
    hashed = hash_password(test_pwd)
    print(f"Password: {test_pwd}")
    print(f"Hash: {hashed}")
    print(f"Verify: {verify_password(test_pwd, hashed)}")
    print(f"Wrong: {verify_password('wrong', hashed)}")
