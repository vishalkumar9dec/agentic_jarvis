#!/bin/bash
# Start Oxygen A2A Agent on port 8002

echo "Starting Oxygen A2A Agent on port 8002..."

# Check if port is already in use
if lsof -ti:8002 > /dev/null 2>&1; then
    echo "⚠ Port 8002 is already in use. Cleaning up existing processes..."
    lsof -ti:8002 | xargs kill -9 2>/dev/null
    sleep 1
    echo "✓ Port 8002 cleaned"
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

# Check if .env file exists for Oxygen agent
if [ ! -f "remote_agent/oxygen_agent/.env" ]; then
    echo "⚠ Warning: .env file not found for Oxygen agent"
    echo "Creating .env from template..."

    if [ -f "remote_agent/oxygen_agent/.env.template" ]; then
        cp remote_agent/oxygen_agent/.env.template remote_agent/oxygen_agent/.env
        echo "✓ Created remote_agent/oxygen_agent/.env from template"
        echo ""
        echo "⚠ IMPORTANT: Please edit remote_agent/oxygen_agent/.env and add your GOOGLE_API_KEY"
        echo "Press Enter to continue or Ctrl+C to exit and configure .env first..."
        read
    else
        echo "❌ Error: Template file not found at remote_agent/oxygen_agent/.env.template"
        exit 1
    fi
fi

# Check if agent file exists
if [ ! -f "remote_agent/oxygen_agent/agent.py" ]; then
    echo "❌ Error: Agent file not found at remote_agent/oxygen_agent/agent.py"
    exit 1
fi

# Start the agent
echo "Starting Oxygen A2A agent..."
.venv/bin/python -m uvicorn remote_agent.oxygen_agent.agent:a2a_app --host localhost --port 8002

# Note: The agent runs in foreground. Use Ctrl+C to stop.
