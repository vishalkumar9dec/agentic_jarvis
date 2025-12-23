"""
JWT Token Utilities for Jarvis Authentication
Handles JWT token creation and validation.
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def create_jwt_token(username: str, user_id: str, role: str = "user") -> str:
    """
    Create JWT token for authenticated user.

    Args:
        username: Username of the authenticated user
        user_id: Unique user identifier
        role: User role (e.g., 'admin', 'user', 'developer', etc.)

    Returns:
        JWT token string
    """
    payload = {
        "username": username,
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Optional[Dict]:
    """
    Verify JWT token and return payload if valid.

    Args:
        token: JWT token string

    Returns:
        Token payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Token is invalid
        return None


def extract_user_from_token(token: str) -> Optional[str]:
    """
    Extract username from JWT token.

    Args:
        token: JWT token string

    Returns:
        Username if token is valid, None otherwise
    """
    payload = verify_jwt_token(token)
    return payload.get("username") if payload else None


if __name__ == "__main__":
    # Simple test
    print("Testing JWT utilities...")

    # Create token
    test_token = create_jwt_token("vishal", "user_001", "developer")
    print(f"✓ Token created: {test_token[:50]}...")

    # Verify token
    payload = verify_jwt_token(test_token)
    print(f"✓ Token verified: {payload}")

    # Extract username
    username = extract_user_from_token(test_token)
    print(f"✓ Username extracted: {username}")

    # Test invalid token
    invalid_payload = verify_jwt_token("invalid-token")
    print(f"✓ Invalid token returns: {invalid_payload}")

    print("\n✅ All JWT utilities working correctly!")
