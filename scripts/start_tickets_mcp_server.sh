#!/bin/bash
# Start Tickets MCP Server (Port 5011)
# Phase 2 - Parallel Implementation
# This script starts the NEW MCP-based Tickets server on port 5011
# The existing Toolbox server on port 5001 remains UNCHANGED

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
echo " Starting Tickets MCP Server (Port 5011)"
echo "======================================================================"
echo ""

# Check if port 5011 is already in use
if lsof -Pi :5011 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 5011 is already in use${NC}"
    echo ""
    echo "Process using port 5011:"
    lsof -i :5011
    echo ""
    read -p "Kill existing process and restart? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing process on port 5011...${NC}"
        lsof -ti:5011 | xargs kill -9 2>/dev/null || true
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

echo -e "${GREEN}✓ Starting Tickets MCP Server...${NC}"
echo ""
echo "  Port: 5011"
echo "  MCP Endpoint: http://localhost:5011/mcp"
echo "  Health Check: http://localhost:5011/health"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Start the server
python -m tickets_mcp_server.app
