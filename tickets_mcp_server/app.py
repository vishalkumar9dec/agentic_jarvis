"""
Tickets MCP Server - FastAPI Application
Mounts FastMCP server to HTTP endpoint using FastAPI.

Port: 5011
Protocol: MCP over HTTP (Server-Sent Events)
Phase: 2A - No authentication yet

This application serves the Tickets MCP server over HTTP, allowing
ADK agents to connect via McpToolset with SseConnectionParams.
"""

from tickets_mcp_server.server import mcp
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
    print(" Tickets MCP Server (Phase 2 - Parallel Implementation)")
    print("=" * 70)
    print()
    print("  Port: 5011 (NEW - parallel to existing 5001)")
    print("  Protocol: Model Context Protocol (MCP)")
    print("  MCP Endpoint: http://localhost:5011/mcp")
    print("  Health Check: http://localhost:5011/health")
    print("  Info: http://localhost:5011/info")
    print()
    print("  Phase: 2A - No authentication")
    print("  Tools: 4 public tools available")
    print()
    print("  NOTE: Existing Toolbox server on port 5001 is UNCHANGED")
    print("  NOTE: Authentication will be added in Task 10 (ADK-compliant)")
    print("=" * 70)
    print()

    try:
        uvicorn.run(
            app,
            host="localhost",
            port=5011,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down Tickets MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
