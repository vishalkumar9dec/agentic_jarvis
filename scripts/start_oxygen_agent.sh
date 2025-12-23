#!/bin/bash
# Start Oxygen A2A Agent (Port 8002)

echo "Starting Oxygen A2A Agent..."

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run 'python -m venv .venv' first."
    exit 1
fi

# Kill existing process on port 8002
echo "Checking for existing processes on port 8002..."
lsof -ti:8002 | xargs kill -9 2>/dev/null
sleep 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Start oxygen agent
echo "Starting oxygen agent on port 8002..."
.venv/bin/python -m uvicorn remote_agent.oxygen_agent.agent:a2a_app --host localhost --port 8002 > logs/oxygen_agent.log 2>&1 &

# Wait a moment for service to start
sleep 2

# Check if service is running
if lsof -i:8002 > /dev/null 2>&1; then
    echo "✓ Oxygen Agent started successfully on port 8002"
    echo "  Logs: logs/oxygen_agent.log"
    echo "  URL: http://localhost:8002"
    echo "  Agent Card: http://localhost:8002/.well-known/agent-card.json"
else
    echo "✗ Failed to start Oxygen Agent"
    echo "  Check logs/oxygen_agent.log for errors"
    exit 1
fi
