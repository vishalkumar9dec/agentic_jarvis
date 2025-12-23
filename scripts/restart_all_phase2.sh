#!/bin/bash
# Restart All Phase 2 Services
# This script starts all services required for Phase 2 (JWT Authentication)

echo "========================================"
echo "  Restarting All Phase 2 Services"
echo "========================================"
echo ""

# Change to project root
cd "$(dirname "$0")/.." || exit 1

# Make all scripts executable
chmod +x scripts/*.sh

# Step 1: Start Auth Service (required for authentication)
echo "Step 1/5: Starting Auth Service..."
./scripts/start_auth_service.sh
if [ $? -ne 0 ]; then
    echo "✗ Failed to start Auth Service. Aborting."
    exit 1
fi
echo ""
sleep 1

# Step 2: Start Tickets Toolbox Server
echo "Step 2/5: Starting Tickets Toolbox Server..."
./scripts/start_tickets_server.sh
if [ $? -ne 0 ]; then
    echo "✗ Failed to start Tickets Server. Aborting."
    exit 1
fi
echo ""
sleep 1

# Step 3: Start FinOps Toolbox Server
echo "Step 3/5: Starting FinOps Toolbox Server..."
./scripts/start_finops_server.sh
if [ $? -ne 0 ]; then
    echo "✗ Failed to start FinOps Server. Aborting."
    exit 1
fi
echo ""
sleep 1

# Step 4: Start Oxygen A2A Agent
echo "Step 4/5: Starting Oxygen A2A Agent..."
./scripts/start_oxygen_agent.sh
if [ $? -ne 0 ]; then
    echo "✗ Failed to start Oxygen Agent. Aborting."
    exit 1
fi
echo ""
sleep 1

# Step 5: Start Web UI Server
echo "Step 5/5: Starting Web UI Server..."
./scripts/start_web_ui.sh
if [ $? -ne 0 ]; then
    echo "✗ Failed to start Web UI Server. Aborting."
    exit 1
fi
echo ""

# Summary
echo "========================================"
echo "  All Phase 2 Services Started!"
echo "========================================"
echo ""
echo "Services running:"
echo "  • Auth Service:      http://localhost:9998"
echo "  • Tickets Server:    http://localhost:5001"
echo "  • FinOps Server:     http://localhost:5002"
echo "  • Oxygen Agent:      http://localhost:8002"
echo "  • Web UI:            http://localhost:9999"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:9999/login.html in your browser"
echo "  2. Login with demo account:"
echo "     - Username: vishal | alex | sarah"
echo "     - Password: password123"
echo "  3. Start chatting with Jarvis!"
echo ""
echo "Or use CLI:"
echo "  python main.py"
echo ""
echo "To check service health:"
echo "  ./scripts/check_phase2_services.sh"
echo ""
echo "Logs are available in logs/ directory"
