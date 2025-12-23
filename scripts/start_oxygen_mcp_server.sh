#!/bin/bash
# Start Oxygen MCP Server (Port 8012)
# Phase 2 - Parallel Implementation
# This script starts the NEW MCP-based Oxygen server on port 8012
# The existing A2A agent on port 8002 remains UNCHANGED

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "======================================================================"
echo " Starting Oxygen MCP Server (Port 8012)"
echo "======================================================================"
echo ""

# Check if port 8012 is already in use
if lsof -Pi :8012 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8012 is already in use${NC}"
    echo ""
    echo "Process using port 8012:"
    lsof -i :8012
    echo ""
    read -p "Kill existing process and restart? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing process on port 8012...${NC}"
        lsof -ti:8012 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${RED}Cancelled. Please stop the existing process first.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment${NC}"
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo -e "${RED}✗ Virtual environment not found at $PROJECT_ROOT/.venv${NC}"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if FastMCP is installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo -e "${RED}✗ FastMCP not installed${NC}"
    echo "Please install dependencies:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${GREEN}✓ Starting Oxygen MCP Server...${NC}"
echo ""
echo "  Port: 8012"
echo "  MCP Endpoint: http://localhost:8012/mcp"
echo "  Health Check: http://localhost:8012/health"
echo "  Features: Learning & Development Platform"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Start the server
python -m oxygen_mcp_server.app
