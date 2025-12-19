"""Web interface for Agentic Jarvis using ADK web UI."""

import os
from dotenv import load_dotenv
from google.adk.cli.fast_api import get_fast_api_app

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not found in environment variables")
    print("Please copy .env.template to .env and add your Google API key")
    exit(1)

# Get the directory containing the agents (project root)
# The ADK expects agents_dir to contain agent folders, not to be an agent folder itself
AGENTS_DIR = os.path.dirname(__file__)  # This is the project root
print(f"Using agents directory: {AGENTS_DIR}")

# Create the FastAPI app with ADK web UI
app = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    allow_origins=["*"],  # Allow all origins for development
    web=True  # Enable the web UI
)

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print(" Agentic Jarvis - Web Interface")
    print("=" * 70)
    print()
    print("Starting web server...")
    print()
    print("IMPORTANT: Make sure these services are running first:")
    print("  1. Tickets Toolbox Server (port 5001)")
    print("     → Run: ./scripts/restart_all.sh")
    print()
    print("  2. FinOps Toolbox Server (port 5002)")
    print("     → Automatically started by restart_all.sh")
    print()
    print("  3. Oxygen A2A Agent (port 8002)")
    print("     → Automatically started by restart_all.sh")
    print()
    print("=" * 70)
    print()
    print("Web UI will be available at:")
    print("  → http://localhost:9999/dev-ui")
    print()
    print("API endpoints will be available at:")
    print("  → http://localhost:9999/docs")
    print()
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=9999)
