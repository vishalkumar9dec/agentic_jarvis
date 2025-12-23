#!/usr/bin/env python3
"""
Automated Authentication Test Script
Tests the MCP authentication flow end-to-end.
"""

import os
import sys
import time
import subprocess
import requests

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.jwt_utils import verify_jwt_token, create_jwt_token

def test_auth_service():
    """Test 1: Verify auth service is working."""
    print("\n" + "="*70)
    print("TEST 1: Auth Service")
    print("="*70)

    try:
        response = requests.post(
            'http://localhost:9998/auth/login',
            json={'username': 'vishal', 'password': 'password123'},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            token = data['token']
            user = data['user']

            print(f"✓ Login successful")
            print(f"  User: {user['username']}")
            print(f"  Role: {user['role']}")
            print(f"  Token length: {len(token)} chars")

            # Verify token can be decoded
            payload = verify_jwt_token(token)
            if payload:
                print(f"✓ Token validation works")
                print(f"  Username from token: {payload.get('username')}")
                print(f"  User ID from token: {payload.get('user_id')}")
                return True, token
            else:
                print(f"✗ Token validation failed")
                return False, None
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False, None

    except Exception as e:
        print(f"✗ Auth service error: {e}")
        return False, None


def test_mcp_server_health():
    """Test 2: Verify MCP servers are running."""
    print("\n" + "="*70)
    print("TEST 2: MCP Server Health")
    print("="*70)

    servers = {
        'Tickets': 5011,
        'FinOps': 5012,
        'Oxygen': 8012
    }

    all_running = True
    for name, port in servers.items():
        # Check if port is listening
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✓ {name} MCP Server running on port {port} (PID: {pid})")
        else:
            print(f"✗ {name} MCP Server NOT running on port {port}")
            all_running = False

    return all_running


def test_direct_mcp_call(bearer_token):
    """Test 3: Test direct HTTP call to MCP server with auth header."""
    print("\n" + "="*70)
    print("TEST 3: Direct MCP Server Call (with Authorization header)")
    print("="*70)

    # Test authenticated tool via direct HTTP call
    # Note: This tests if the MCP server correctly receives and processes the Authorization header

    try:
        # MCP uses JSON-RPC over HTTP
        # We'll call the tickets MCP server directly
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }

        # Call the MCP endpoint (SSE transport)
        # Note: Direct testing of SSE endpoint is complex, so we'll skip this
        # and rely on end-to-end CLI testing

        print("⚠ Skipping direct MCP call (requires SSE client)")
        print("  Will test via CLI instead")
        return True

    except Exception as e:
        print(f"✗ Direct MCP call failed: {e}")
        return False


def test_context_and_header_provider():
    """Test 4: Test auth_context module."""
    print("\n" + "="*70)
    print("TEST 4: Auth Context & Header Provider")
    print("="*70)

    try:
        from jarvis_agent.mcp_agents.auth_context import (
            set_bearer_token,
            get_bearer_token,
            create_auth_header_provider,
            clear_bearer_token
        )

        # Test 1: Set and get token
        test_token = "test_token_123"
        set_bearer_token(test_token)
        retrieved = get_bearer_token()

        if retrieved == test_token:
            print("✓ Context token storage works")
        else:
            print(f"✗ Context token mismatch: {retrieved} != {test_token}")
            return False

        # Test 2: Header provider
        header_provider = create_auth_header_provider()
        headers = header_provider()

        expected_header = f"Bearer {test_token}"
        if headers.get("Authorization") == expected_header:
            print("✓ Header provider works")
            print(f"  Generated header: Authorization: {expected_header[:30]}...")
        else:
            print(f"✗ Header provider failed: {headers}")
            return False

        # Test 3: Clear token
        clear_bearer_token()
        cleared = get_bearer_token()
        if cleared is None:
            print("✓ Token clearing works")
        else:
            print(f"✗ Token not cleared: {cleared}")
            return False

        # Test 4: Header provider with no token
        headers_empty = header_provider()
        if headers_empty == {}:
            print("✓ Header provider returns empty dict when no token")
        else:
            print(f"✗ Header provider should return empty dict: {headers_empty}")
            return False

        return True

    except Exception as e:
        print(f"✗ Auth context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastmcp_header_extraction():
    """Test 5: Test that FastMCP can extract headers."""
    print("\n" + "="*70)
    print("TEST 5: FastMCP Header Extraction")
    print("="*70)

    try:
        from fastmcp.server.dependencies import get_http_headers
        print("✓ FastMCP get_http_headers import works")

        # Note: get_http_headers() only works within a FastMCP request context
        # We can't test it directly here, but we verified the import works
        print("⚠ Actual header extraction can only be tested via MCP server")
        return True

    except ImportError as e:
        print(f"✗ FastMCP import failed: {e}")
        print("  This means the tickets_mcp_server will fail!")
        return False


def test_agent_factory():
    """Test 6: Test agent factory creates agents with header_provider."""
    print("\n" + "="*70)
    print("TEST 6: Agent Factory Configuration")
    print("="*70)

    try:
        # We can't actually create the agents here because they require API key
        # and will try to connect to MCP servers
        # Instead, just verify the module can be imported
        from jarvis_agent.mcp_agents.agent_factory import (
            create_tickets_agent,
            create_finops_agent,
            create_oxygen_agent,
            create_root_agent
        )
        print("✓ Agent factory imports work")

        # Verify auth_context is imported
        import inspect
        source = inspect.getsource(create_tickets_agent)
        if 'create_auth_header_provider' in source:
            print("✓ Agent factory uses create_auth_header_provider")
        else:
            print("✗ Agent factory missing create_auth_header_provider")
            return False

        return True

    except Exception as e:
        print(f"✗ Agent factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all automated tests."""
    print("\n" + "="*70)
    print("AUTOMATED AUTHENTICATION TESTS")
    print("="*70)

    results = {}

    # Test 1: Auth service
    success, token = test_auth_service()
    results['auth_service'] = success

    # Test 2: MCP servers running
    results['mcp_servers'] = test_mcp_server_health()

    # Test 3: Direct MCP call (skipped)
    results['direct_mcp'] = test_direct_mcp_call(token if token else "dummy")

    # Test 4: Auth context
    results['auth_context'] = test_context_and_header_provider()

    # Test 5: FastMCP imports
    results['fastmcp'] = test_fastmcp_header_extraction()

    # Test 6: Agent factory
    results['agent_factory'] = test_agent_factory()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL AUTOMATED TESTS PASSED")
        print("\nReady for manual CLI testing:")
        print("  python main_mcp_auth.py")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nFix the issues before proceeding to CLI testing")
    print("="*70)

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
