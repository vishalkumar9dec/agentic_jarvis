"""
Oxygen MCP Server - FastAPI Application
Mounts FastMCP server to HTTP endpoint using FastAPI.

Port: 8012
Protocol: MCP over HTTP (Server-Sent Events)
Phase: 2A - No authentication yet

This application serves the Oxygen MCP server over HTTP, allowing
ADK agents to connect via McpToolset with SseConnectionParams.
"""

from oxygen_mcp_server.server import mcp
import uvicorn
import sys

# =============================================================================
# Create MCP Application
# =============================================================================
# Use FastMCP's http_app() with SSE transport for ADK McpToolset compatibility

app = mcp.http_app(path="/mcp", transport="sse")


# =============================================================================
# Application Entry Point
# =============================================================================

def main():
    """Main entry point for running the MCP server."""
    print("=" * 70)
    print(" Oxygen MCP Server (Phase 2 - Parallel Implementation)")
    print("=" * 70)
    print()
    print("  Port: 8012 (NEW - parallel to existing 8002 A2A)")
    print("  Protocol: Model Context Protocol (MCP)")
    print("  MCP Endpoint: http://localhost:8012/mcp")
    print("  Health Check: http://localhost:8012/health")
    print("  Info: http://localhost:8012/info")
    print()
    print("  Phase: 2A - No authentication")
    print("  Tools: 4 public learning platform tools")
    print("  Features: Course tracking, exam management, progress analytics")
    print()
    print("  NOTE: Existing A2A agent on port 8002 is UNCHANGED")
    print("  NOTE: Authentication will be added in Task 11 (ADK-compliant)")
    print("=" * 70)
    print()

    try:
        uvicorn.run(
            app,
            host="localhost",
            port=8012,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down Oxygen MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
