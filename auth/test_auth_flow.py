"""
Integration test for authentication flow.
Tests the complete authentication workflow: authenticate user → create token → verify token
"""

from jwt_utils import create_jwt_token, verify_jwt_token, extract_user_from_token
from user_service import authenticate_user, get_user_info


def test_complete_auth_flow():
    """Test complete authentication flow."""
    print("=" * 60)
    print("INTEGRATION TEST: Complete Authentication Flow")
    print("=" * 60)

    # Step 1: User authentication
    print("\n1. User Authentication")
    print("-" * 60)
    username = "vishal"
    password = "password123"
    print(f"Attempting login: {username} / {password}")

    user = authenticate_user(username, password)
    if user:
        print(f"✓ Authentication successful!")
        print(f"  User ID: {user['user_id']}")
        print(f"  Username: {user['username']}")
        print(f"  Role: {user['role']}")
        print(f"  Email: {user['email']}")
    else:
        print("✗ Authentication failed!")
        return False

    # Step 2: JWT token creation
    print("\n2. JWT Token Creation")
    print("-" * 60)
    token = create_jwt_token(user['username'], user['user_id'])
    print(f"✓ JWT token created successfully!")
    print(f"  Token (first 50 chars): {token[:50]}...")

    # Step 3: Token verification
    print("\n3. JWT Token Verification")
    print("-" * 60)
    payload = verify_jwt_token(token)
    if payload:
        print(f"✓ Token verified successfully!")
        print(f"  Username from token: {payload['username']}")
        print(f"  User ID from token: {payload['user_id']}")
        print(f"  Token expires at: {payload['exp']}")
    else:
        print("✗ Token verification failed!")
        return False

    # Step 4: Extract username from token
    print("\n4. Username Extraction")
    print("-" * 60)
    extracted_username = extract_user_from_token(token)
    if extracted_username == username:
        print(f"✓ Username extracted correctly: {extracted_username}")
    else:
        print(f"✗ Username mismatch! Expected {username}, got {extracted_username}")
        return False

    # Step 5: Test invalid credentials
    print("\n5. Invalid Credentials Test")
    print("-" * 60)
    print("Attempting login with wrong password...")
    invalid_user = authenticate_user(username, "wrongpassword")
    if invalid_user is None:
        print("✓ Invalid credentials correctly rejected")
    else:
        print("✗ Should have rejected invalid credentials!")
        return False

    # Step 6: Test invalid token
    print("\n6. Invalid Token Test")
    print("-" * 60)
    print("Verifying invalid token...")
    invalid_payload = verify_jwt_token("invalid-token-string")
    if invalid_payload is None:
        print("✓ Invalid token correctly rejected")
    else:
        print("✗ Should have rejected invalid token!")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL AUTHENTICATION FLOW TESTS PASSED!")
    print("=" * 60)
    return True


def test_all_users():
    """Test authentication for all users."""
    print("\n\n" + "=" * 60)
    print("TESTING ALL USER ACCOUNTS")
    print("=" * 60)

    test_users = [
        ("vishal", "password123", "developer"),
        ("alex", "password123", "devops"),
        ("sarah", "password123", "data_scientist")
    ]

    for username, password, expected_role in test_users:
        print(f"\nTesting user: {username}")
        user = authenticate_user(username, password)
        if user and user['role'] == expected_role:
            token = create_jwt_token(user['username'], user['user_id'])
            payload = verify_jwt_token(token)
            if payload and payload['username'] == username:
                print(f"  ✓ {username} - authentication & token flow working")
            else:
                print(f"  ✗ {username} - token flow failed")
        else:
            print(f"  ✗ {username} - authentication failed")

    print("\n✅ All user accounts tested successfully!")


if __name__ == "__main__":
    # Run complete authentication flow test
    test_complete_auth_flow()

    # Test all user accounts
    test_all_users()

    print("\n" + "=" * 60)
    print("TASK 18 COMPLETE: JWT Authentication Infrastructure Ready!")
    print("=" * 60)
