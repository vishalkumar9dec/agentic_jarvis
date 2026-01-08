#!/bin/bash

# Start LiteLLM Agent Gateway
# This script launches the LiteLLM gateway that exposes the Agentic Jarvis A2A agents

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GATEWAY_PORT=8090
CONFIG_FILE="litellm_config.yaml"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}Starting LiteLLM Agent Gateway...${NC}"

# Check if config file exists
if [ ! -f "$PROJECT_ROOT/$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file $CONFIG_FILE not found!${NC}"
    exit 1
fi

# Check if port is already in use
if lsof -Pi :$GATEWAY_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port $GATEWAY_PORT is already in use${NC}"
    echo -e "${YELLOW}Killing existing process...${NC}"
    lsof -ti:$GATEWAY_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${GREEN}Loading environment variables from .env${NC}"
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Check required environment variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}Warning: GOOGLE_API_KEY not set. LLM routing may not work.${NC}"
fi

if [ -z "$LITELLM_MASTER_KEY" ]; then
    echo -e "${YELLOW}Warning: LITELLM_MASTER_KEY not set. Using default: sk-1234${NC}"
    export LITELLM_MASTER_KEY="sk-1234"
fi

# Start the gateway
echo -e "${GREEN}Starting LiteLLM gateway on port $GATEWAY_PORT...${NC}"
echo -e "${GREEN}Configuration: $CONFIG_FILE${NC}"

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Launch LiteLLM with config
litellm --config "$CONFIG_FILE" --port $GATEWAY_PORT --host 0.0.0.0

# Note: This script runs in foreground. Use & or run in separate terminal for background execution
