"""
User Service for Jarvis Authentication
Handles user authentication and user data management.
"""

import hashlib
from typing import Optional, Dict

# Mock user database
# In production, this would be a real database with properly hashed passwords
USERS_DB = {
    "vishal": {
        "user_id": "user_001",
        "username": "vishal",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "role": "developer",
        "email": "vishal@company.com"
    },
    "happy": {
        "user_id": "user_002",
        "username": "happy",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "role": "developer",
        "email": "happy@company.com"
    },
    "alex": {
        "user_id": "user_003",
        "username": "alex",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "role": "devops",
        "email": "alex@company.com"
    },
    "sarah": {
        "user_id": "user_004",
        "username": "sarah",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "role": "data_scientist",
        "email": "sarah@company.com"
    },
    "admin": {
        "user_id": "user_admin",
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "email": "admin@company.com"
    }
}


def _hash_password(password: str) -> str:
    """
    Hash password using SHA256.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate user with username and password.

    Args:
        username: Username to authenticate
        password: Plain text password

    Returns:
        User info dict if authentication successful, None otherwise
    """
    user = USERS_DB.get(username)

    if not user:
        return None

    password_hash = _hash_password(password)

    if password_hash != user["password_hash"]:
        return None

    # Return user info without password hash
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "email": user["email"]
    }


def get_user_info(username: str) -> Optional[Dict]:
    """
    Get user information by username.

    Args:
        username: Username to look up

    Returns:
        User info dict if user exists, None otherwise
    """
    user = USERS_DB.get(username)

    if not user:
        return None

    # Return user info without password hash
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "email": user["email"]
    }


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """
    Get user information by user ID.

    Args:
        user_id: User ID to look up

    Returns:
        User info dict if user exists, None otherwise
    """
    for user in USERS_DB.values():
        if user["user_id"] == user_id:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"],
                "email": user["email"]
            }

    return None


if __name__ == "__main__":
    # Simple test
    print("Testing User Service...\n")

    # Test 1: Valid authentication
    print("Test 1: Valid authentication")
    user = authenticate_user("vishal", "password123")
    if user:
        print(f"✓ Authentication successful: {user}")
    else:
        print("✗ Authentication failed")

    # Test 2: Invalid password
    print("\nTest 2: Invalid password")
    user = authenticate_user("vishal", "wrongpassword")
    if user is None:
        print("✓ Invalid password correctly rejected")
    else:
        print("✗ Should have rejected invalid password")

    # Test 3: Invalid username
    print("\nTest 3: Invalid username")
    user = authenticate_user("nonexistent", "password123")
    if user is None:
        print("✓ Invalid username correctly rejected")
    else:
        print("✗ Should have rejected invalid username")

    # Test 4: Get user info
    print("\nTest 4: Get user info")
    user_info = get_user_info("alex")
    if user_info:
        print(f"✓ User info retrieved: {user_info}")
    else:
        print("✗ Failed to retrieve user info")

    # Test 5: Get user by ID
    print("\nTest 5: Get user by ID")
    user_info = get_user_by_id("user_003")
    if user_info and user_info["username"] == "sarah":
        print(f"✓ User found by ID: {user_info}")
    else:
        print("✗ Failed to find user by ID")

    print("\n✅ All User Service tests completed!")
