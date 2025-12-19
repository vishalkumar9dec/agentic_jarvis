#!/bin/bash

# Start the ADK Web UI for Agentic Jarvis

echo "========================================"
echo " Starting Jarvis Web Interface"
echo "========================================"
echo ""

# Kill any existing processes on port 9999
if lsof -ti:9999 > /dev/null 2>&1; then
    echo "Cleaning up existing processes on port 9999..."
    lsof -ti:9999 | xargs kill -9 2>/dev/null
    sleep 1
    echo "✓ Port 9999 cleared"
    echo ""
fi

# Check if required services are running
echo "Checking required services..."
echo ""

services_ok=true

if ! lsof -ti:5001 > /dev/null 2>&1; then
    echo "❌ Tickets server is not running on port 5001"
    services_ok=false
fi

if ! lsof -ti:5002 > /dev/null 2>&1; then
    echo "❌ FinOps server is not running on port 5002"
    services_ok=false
fi

if ! lsof -ti:8002 > /dev/null 2>&1; then
    echo "❌ Oxygen agent is not running on port 8002"
    services_ok=false
fi

if [ "$services_ok" = false ]; then
    echo ""
    echo "Please start all services first:"
    echo "  ./scripts/restart_all.sh"
    echo ""
    exit 1
fi

echo "✓ All required services are running"
echo ""
echo "========================================"
echo "Starting web server on port 9999..."
echo ""
echo "Web UI will be available at:"
echo "  http://localhost:9999/dev-ui"
echo ""
echo "API docs available at:"
echo "  http://localhost:9999/docs"
echo "========================================"
echo ""

.venv/bin/python web.py
