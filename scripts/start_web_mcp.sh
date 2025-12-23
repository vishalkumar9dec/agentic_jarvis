#!/bin/bash

echo "========================================"
echo " Jarvis MCP Web UI (Port 9990)"
echo " Phase 2 - Part A: No Auth"
echo "========================================"
echo ""

# Kill existing process on port 9990
if lsof -ti:9990 > /dev/null 2>&1; then
    echo "Cleaning up existing process on port 9990..."
    lsof -ti:9990 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Check if MCP servers are running
echo "Checking MCP servers..."
services_ok=true

if ! lsof -ti:5011 > /dev/null 2>&1; then
    echo "❌ Tickets MCP server not running on port 5011"
    services_ok=false
fi

if ! lsof -ti:5012 > /dev/null 2>&1; then
    echo "❌ FinOps MCP server not running on port 5012"
    services_ok=false
fi

if ! lsof -ti:8012 > /dev/null 2>&1; then
    echo "❌ Oxygen MCP server not running on port 8012"
    services_ok=false
fi

if [ "$services_ok" = false ]; then
    echo ""
    echo "⚠️  WARNING: Some MCP servers are not running"
    echo ""
    echo "The Web UI will start, but you won't be able to query agents"
    echo "until all MCP servers are running."
    echo ""
    echo "To start all MCP servers, run:"
    echo "  # Terminal 1:"
    echo "  source .venv/bin/activate && python -m tickets_mcp_server.app"
    echo ""
    echo "  # Terminal 2:"
    echo "  source .venv/bin/activate && python -m finops_mcp_server.app"
    echo ""
    echo "  # Terminal 3:"
    echo "  source .venv/bin/activate && python -m oxygen_mcp_server.app"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
else
    echo "✓ All MCP servers running"
fi

echo ""
echo "Starting MCP Web UI..."
echo "  → http://localhost:9990/"
echo ""

source .venv/bin/activate
python web_ui/server_mcp.py
