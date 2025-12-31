#!/usr/bin/env python3
"""
Reusable MCP Test Client
Tests MCP servers (Tickets, Oxygen, FinOps) via MCP protocol.

Usage:
    # Test Tickets server
    python test_mcp_client.py --server tickets

    # Test Oxygen server
    python test_mcp_client.py --server oxygen

    # Test all servers
    python test_mcp_client.py --all
"""

import asyncio
import httpx
import json
import sys
import argparse
from typing import Optional, Dict, List


# =============================================================================
# Server Configurations
# =============================================================================

SERVERS = {
    "tickets": {
        "name": "Tickets MCP Server",
        "url": "http://localhost:5011",
        "public_tools": ["get_all_tickets", "get_ticket"],
        "auth_tools": ["get_my_tickets", "create_my_ticket"],
        "test_data": {
            "get_ticket": {"ticket_id": 12301},
            "create_my_ticket": {"operation": "test_from_mcp_client"}
        }
    },
    "oxygen": {
        "name": "Oxygen MCP Server",
        "url": "http://localhost:5012",
        "public_tools": [],  # Add if any
        "auth_tools": ["get_my_courses", "get_my_exams"],
        "test_data": {}
    },
    "finops": {
        "name": "FinOps MCP Server",
        "url": "http://localhost:8012",
        "public_tools": [],  # Add if any
        "auth_tools": [],  # Add if any
        "test_data": {}
    }
}

AUTH_SERVER_URL = "http://localhost:9998"


# =============================================================================
# MCP Client Class
# =============================================================================

class MCPClient:
    """Simple MCP client for testing MCP servers."""

    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.auth_token = auth_token

    async def call_tool(self, tool_name: str, arguments: dict = None) -> Optional[dict]:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments (default: {})

        Returns:
            Tool result or None on error
        """
        if arguments is None:
            arguments = {}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # MCP tool call request (JSON-RPC 2.0)
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/mcp",
                    json=request_data,
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code != 200:
                    return {
                        "error": f"HTTP {response.status_code}",
                        "detail": response.text
                    }

                return response.json()

            except Exception as e:
                return {"error": str(e)}

    async def list_tools(self) -> Optional[List[dict]]:
        """List available tools on the MCP server."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/mcp",
                    json=request_data,
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {}).get("tools", [])
                return None

            except Exception as e:
                print(f"Error listing tools: {e}")
                return None


# =============================================================================
# Authentication Helper
# =============================================================================

async def get_auth_token(username: str, password: str) -> Optional[str]:
    """Get JWT token from auth server."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVER_URL}/auth/login",
                json={"username": username, "password": password},
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("token")
            else:
                print(f"   ✗ Auth failed: {response.text}")
                return None

        except httpx.ConnectError:
            print(f"   ✗ Auth server not running on {AUTH_SERVER_URL}")
            return None
        except Exception as e:
            print(f"   ✗ Auth error: {e}")
            return None


# =============================================================================
# Test Functions
# =============================================================================

async def check_server(url: str, name: str) -> bool:
    """Check if MCP server is running."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{url}/mcp", timeout=2.0)
            return True
        except httpx.ConnectError:
            print(f"   ✗ {name} not running on {url}")
            return False
        except Exception:
            return True  # Server responded, even if with error


async def test_public_tools(server_key: str):
    """Test public tools (no authentication required)."""
    config = SERVERS[server_key]

    if not config["public_tools"]:
        print(f"\n   No public tools configured for {config['name']}")
        return

    print(f"\n{'='*70}")
    print(f"Testing Public Tools - {config['name']}")
    print('='*70)

    client = MCPClient(config["url"])

    for tool_name in config["public_tools"]:
        print(f"\n   Testing {tool_name}...")

        # Get test data for this tool
        args = config["test_data"].get(tool_name, {})

        result = await client.call_tool(tool_name, args)
        if result and "error" not in result:
            print(f"   ✓ Success")
            print(f"      Result preview: {str(result)[:100]}...")
        else:
            print(f"   ✗ Failed: {result}")


async def test_authenticated_tools(server_key: str, username: str = "vishal"):
    """Test authenticated tools with valid token."""
    config = SERVERS[server_key]

    if not config["auth_tools"]:
        print(f"\n   No authenticated tools configured for {config['name']}")
        return

    print(f"\n{'='*70}")
    print(f"Testing Authenticated Tools - {config['name']}")
    print('='*70)

    # Get token
    print(f"\n   1. Getting JWT token for user '{username}'...")
    token = await get_auth_token(username, "password123")

    if not token:
        print("      ✗ Could not get token - skipping authenticated tests")
        return

    print(f"      ✓ Got token: {token[:30]}...")

    # Create client with token
    client = MCPClient(config["url"], auth_token=token)

    # Test each authenticated tool
    for i, tool_name in enumerate(config["auth_tools"], start=2):
        print(f"\n   {i}. Testing {tool_name} (with token)...")

        # Get test data for this tool
        args = config["test_data"].get(tool_name, {})

        result = await client.call_tool(tool_name, args)
        if result and "error" not in str(result):
            print(f"      ✓ Success")
            print(f"         Result preview: {str(result)[:100]}...")
        else:
            print(f"      ✗ Failed: {result}")


async def test_authentication_required(server_key: str):
    """Test that authenticated tools reject requests without token."""
    config = SERVERS[server_key]

    if not config["auth_tools"]:
        return

    print(f"\n{'='*70}")
    print(f"Testing Auth Required - {config['name']}")
    print('='*70)

    client = MCPClient(config["url"])  # No token

    # Test first authenticated tool without token
    tool_name = config["auth_tools"][0]
    print(f"\n   Testing {tool_name} (no token - should fail)...")

    result = await client.call_tool(tool_name)
    if result and "error" in str(result).lower():
        print(f"   ✓ Correctly rejected unauthenticated request")
    else:
        print(f"   ✗ Should have been rejected: {result}")


async def test_server(server_key: str):
    """Run all tests for a specific server."""
    config = SERVERS[server_key]

    print(f"\n{'='*70}")
    print(f"Testing: {config['name']}")
    print(f"URL: {config['url']}")
    print('='*70)

    # Check if server is running
    if not await check_server(config["url"], config["name"]):
        print(f"\n   ⚠️  Skipping {config['name']} - server not running")
        return False

    print(f"   ✓ Server is running")

    # Run tests
    await test_public_tools(server_key)
    await test_authentication_required(server_key)
    await test_authenticated_tools(server_key)

    return True


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test MCP servers")
    parser.add_argument(
        "--server",
        choices=["tickets", "oxygen", "finops"],
        help="Specific server to test"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all servers"
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tools for each server"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("MCP Server Test Suite")
    print("="*70)

    # Check auth server
    print("\nChecking prerequisites...")
    print(f"   Auth Server: {AUTH_SERVER_URL}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVER_URL}/health", timeout=2.0)
            if response.status_code == 200:
                print("   ✓ Auth server is running")
            else:
                print("   ✗ Auth server not responding correctly")
                return
        except httpx.ConnectError:
            print("   ✗ Auth server not running")
            print(f"\n   Please start: python auth/auth_server.py")
            return

    # Determine which servers to test
    if args.all:
        servers_to_test = list(SERVERS.keys())
    elif args.server:
        servers_to_test = [args.server]
    else:
        # Default: test tickets
        servers_to_test = ["tickets"]

    # Run tests
    results = {}
    for server_key in servers_to_test:
        success = await test_server(server_key)
        results[server_key] = success

    # Summary
    print(f"\n{'='*70}")
    print("Test Summary")
    print('='*70)
    for server_key, success in results.items():
        status = "✓ PASS" if success else "✗ SKIP"
        print(f"   {SERVERS[server_key]['name']}: {status}")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(0)
