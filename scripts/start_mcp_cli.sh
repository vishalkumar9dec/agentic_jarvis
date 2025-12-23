#!/bin/bash
# Start Jarvis MCP CLI
# Phase 2 - Parallel Implementation
# This script starts the NEW MCP-based CLI
# The existing main.py CLI remains UNCHANGED

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
echo " Starting Jarvis MCP CLI"
echo "======================================================================"
echo ""

# Check if MCP servers are running
echo "Checking MCP servers..."
all_running=true

if ! curl -s http://localhost:5011/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Tickets MCP server not running on port 5011${NC}"
    all_running=false
else
    echo -e "${GREEN}✓ Tickets MCP server running${NC}"
fi

if ! curl -s http://localhost:5012/health > /dev/null 2>&1; then
    echo -e "${RED}✗ FinOps MCP server not running on port 5012${NC}"
    all_running=false
else
    echo -e "${GREEN}✓ FinOps MCP server running${NC}"
fi

if ! curl -s http://localhost:8012/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Oxygen MCP server not running on port 8012${NC}"
    all_running=false
else
    echo -e "${GREEN}✓ Oxygen MCP server running${NC}"
fi

if [ "$all_running" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some MCP servers are not running${NC}"
    echo ""
    echo "Please start all MCP servers first:"
    echo "  Terminal 1: ./scripts/start_tickets_mcp_server.sh"
    echo "  Terminal 2: ./scripts/start_finops_mcp_server.sh"
    echo "  Terminal 3: ./scripts/start_oxygen_mcp_server.sh"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Cancelled.${NC}"
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

# Change to project root
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}✓ Starting Jarvis MCP CLI...${NC}"
echo ""

# Start the CLI
python main_mcp.py
