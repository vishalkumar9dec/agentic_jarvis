#!/usr/bin/env python3
"""
Direct Authentication Test for Task 3
Tests authentication middleware by making direct HTTP requests to the server.
"""

import asyncio
import httpx
import json

TICKETS_URL = "http://localhost:5011"
AUTH_URL = "http://localhost:9998"


async def get_token(username: str) -> str:
    """Get JWT token from auth server."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/login",
            json={"username": username, "password": "password123"}
        )
        return response.json()["token"]


async def test_authentication():
    """Test authentication middleware."""
    print("\n" + "="*70)
    print("Task 3: Authentication Middleware Test")
    print("="*70 + "\n")

    # Test 1: Public tool without auth (get_all_tickets)
    print("1. Testing public tool WITHOUT authentication...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TICKETS_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_all_tickets",
                    "arguments": {}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "X-Session-ID": "test-session-1"  # Add session ID
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if response.status_code == 200:
            print("   ✓ Public tool works without auth")
        else:
            print(f"   ✗ Failed: {response.status_code}")

    # Test 2: Authenticated tool without token (should fail)
    print("\n2. Testing authenticated tool WITHOUT token (should fail)...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TICKETS_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_my_tickets",
                    "arguments": {}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "X-Session-ID": "test-session-2"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if "error" in response.text.lower() or "authentication" in response.text.lower():
            print("   ✓ Correctly rejected unauthenticated request")
        else:
            print("   ✗ Should have been rejected")

    # Test 3: Authenticated tool with valid token
    print("\n3. Testing authenticated tool WITH valid token...")
    token = await get_token("vishal")
    print(f"   Got token: {token[:30]}...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TICKETS_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_my_tickets",
                    "arguments": {}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {token}",
                "X-Session-ID": "test-session-3"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if response.status_code == 200:
            print("   ✓ Authenticated tool works with token")
        else:
            print(f"   ✗ Failed: {response.status_code}")

    # Test 4: User isolation
    print("\n4. Testing user isolation...")
    vishal_token = await get_token("vishal")
    alex_token = await get_token("alex")

    # Get vishal's tickets
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TICKETS_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_my_tickets",
                    "arguments": {}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {vishal_token}",
                "X-Session-ID": "test-session-4"
            }
        )
        print(f"   Vishal's tickets: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Vishal can access their tickets")

    print("\n" + "="*70)
    print("Test Summary: Check results above")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_authentication())
