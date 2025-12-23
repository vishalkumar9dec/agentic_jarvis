"""
FinOps MCP Server - FastAPI Application
Mounts FastMCP server to HTTP endpoint using FastAPI.

Port: 5012
Protocol: MCP over HTTP (Server-Sent Events)
Phase: 2A - No authentication yet

This application serves the FinOps MCP server over HTTP, allowing
ADK agents to connect via McpToolset with SseConnectionParams.
"""

from finops_mcp_server.server import mcp
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
    print(" FinOps MCP Server (Phase 2 - Parallel Implementation)")
    print("=" * 70)
    print()
    print("  Port: 5012 (NEW - parallel to existing 5002)")
    print("  Protocol: Model Context Protocol (MCP)")
    print("  MCP Endpoint: http://localhost:5012/mcp")
    print("  Health Check: http://localhost:5012/health")
    print("  Info: http://localhost:5012/info")
    print()
    print("  Phase: 2A - No authentication (costs are org-wide)")
    print("  Tools: 4 public cost analytics tools")
    print("  Providers: AWS, GCP, Azure")
    print()
    print("  NOTE: Existing Toolbox server on port 5002 is UNCHANGED")
    print("  NOTE: Auth infrastructure ready for Task 11 (if needed)")
    print("=" * 70)
    print()

    try:
        uvicorn.run(
            app,
            host="localhost",
            port=5012,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down FinOps MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
