#!/bin/bash
# Start Tickets Toolbox Server on port 5001

echo "Starting Tickets Toolbox Server on port 5001..."

# Check if port is already in use
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠ Port 5001 is already in use. Cleaning up existing processes..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 1
    echo "✓ Port 5001 cleaned"
fi

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found at .venv/"
    echo "Please create a virtual environment first: python -m venv .venv"
    exit 1
fi

# Check if server file exists
if [ ! -f "toolbox_servers/tickets_server/server.py" ]; then
    echo "❌ Error: Server file not found at toolbox_servers/tickets_server/server.py"
    exit 1
fi

# Start the server
echo "Starting server..."
.venv/bin/python toolbox_servers/tickets_server/server.py

# Note: The server runs in foreground. Use Ctrl+C to stop.
