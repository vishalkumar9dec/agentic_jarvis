"""
Jarvis MCP Web Interface (NO AUTH - Part A)
Phase 2 - Parallel Implementation
Port: 9990 (NEW - parallel to 9999)

This web interface connects to the MCP-based agent system for testing
MCP connectivity without authentication.
"""

import sys
import os
import warnings
import logging

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Suppress async cleanup warnings from MCP SSE client
# These are harmless warnings that occur during connection cleanup
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress MCP session cleanup logger warnings
logging.getLogger("google.adk.tools.mcp_tool.mcp_session_manager").setLevel(logging.ERROR)


class StderrFilter:
    """Filter to suppress specific async cleanup errors in stderr."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr

    def write(self, text):
        # Filter out async generator cleanup errors
        if any(keyword in text for keyword in [
            "an error occurred during closing of asynchronous generator",
            "asyncgen:",
            "ExceptionGroup: unhandled errors in a TaskGroup",
            "RuntimeError: generator didn't stop after athrow()",
            "RuntimeError: Attempted to exit cancel scope",
            "Error during disconnected session cleanup"
        ]):
            return  # Suppress these errors
        self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()


# Install stderr filter to suppress async cleanup errors
original_stderr = sys.stderr
sys.stderr = StderrFilter(original_stderr)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jarvis_agent.mcp_agents.agent_factory import create_root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Jarvis MCP Web Interface (No Auth)",
    description="Model Context Protocol web interface for Jarvis AI Assistant",
    version="2.0.0-mcp"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session service
session_service = InMemorySessionService()

# Create MCP agent once for Part A (no per-request creation yet)
print("Initializing Jarvis MCP agent...")
root_agent = create_root_agent()
print("✓ Agent initialized")


class ChatMessage(BaseModel):
    message: str
    session_id: str = "web-session-default"


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve simple chat page (no login in Part A)."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis MCP (Part A - No Auth)</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 900px;
            height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header .subtitle {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
        }

        .header .info {
            font-size: 12px;
            opacity: 0.8;
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }

        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 25px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
        }

        .message-label {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .message-content {
            padding: 15px 18px;
            border-radius: 12px;
            line-height: 1.6;
            max-width: 85%;
        }

        .user .message-label {
            color: #667eea;
            text-align: right;
        }

        .user .message-content {
            background: #667eea;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }

        .assistant .message-label {
            color: #28a745;
        }

        .assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
            white-space: pre-wrap;
        }

        .input-container {
            padding: 20px 25px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 12px;
        }

        #input {
            flex: 1;
            padding: 15px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }

        #input:focus {
            border-color: #667eea;
        }

        button {
            padding: 15px 35px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
            padding: 15px;
            text-align: center;
            color: #666;
            font-style: italic;
        }

        .loading.active {
            display: block;
        }

        /* Scrollbar styling */
        #messages::-webkit-scrollbar {
            width: 8px;
        }

        #messages::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        #messages::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }

        #messages::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Jarvis MCP (Phase 2 - Part A)</h1>
            <div class="subtitle">Model Context Protocol Interface</div>
            <div class="info">
                <strong>NOTE:</strong> No authentication yet. Testing MCP connectivity.<br>
                Connected to: Tickets (5011), FinOps (5012), Oxygen (8012)
            </div>
        </div>

        <div id="messages"></div>
        <div class="loading" id="loading">Jarvis is thinking...</div>

        <div class="input-container">
            <input type="text" id="input" placeholder="Ask Jarvis about tickets, costs, or learning..." autocomplete="off">
            <button onclick="send()" id="sendBtn">Send</button>
        </div>
    </div>

    <script>
        // Define all functions first
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function scrollToBottom() {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addUserMessage(text) {
            const messagesDiv = document.getElementById('messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message user';
            msgDiv.innerHTML = `
                <div class="message-label">You</div>
                <div class="message-content">${escapeHtml(text)}</div>
            `;
            messagesDiv.appendChild(msgDiv);
            scrollToBottom();
        }

        function addAssistantMessage(text) {
            const messagesDiv = document.getElementById('messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message assistant';
            msgDiv.innerHTML = `
                <div class="message-label">Jarvis</div>
                <div class="message-content">${escapeHtml(text)}</div>
            `;
            messagesDiv.appendChild(msgDiv);
            scrollToBottom();
        }

        async function send() {
            const inputField = document.getElementById('input');
            const sendBtn = document.getElementById('sendBtn');
            const loadingDiv = document.getElementById('loading');
            const msg = inputField.value.trim();
            if (!msg) return;

            // Disable input during processing
            inputField.disabled = true;
            sendBtn.disabled = true;
            loadingDiv.classList.add('active');

            // Add user message
            addUserMessage(msg);
            inputField.value = '';

            try {
                // Send to backend
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });

                const data = await response.json();

                if (data.success) {
                    addAssistantMessage(data.response);
                } else {
                    addAssistantMessage('❌ Error: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                addAssistantMessage('❌ Error: Failed to communicate with server. Please check if MCP servers are running.');
                console.error('Error:', error);
            } finally {
                // Re-enable input
                inputField.disabled = false;
                sendBtn.disabled = false;
                loadingDiv.classList.remove('active');
                inputField.focus();
            }
        }

        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            const inputField = document.getElementById('input');

            // Add welcome message
            const welcomeMsg = '👋 Hello! I am Jarvis, your AI assistant. I can help you with:\\n\\n' +
                '• IT Tickets - View and create tickets\\n' +
                '• Cloud Costs - Check AWS, GCP, Azure spending\\n' +
                '• Learning - Track courses and exams\\n\\n' +
                'Try asking: "show all tickets" or "what is the AWS cost?"';
            addAssistantMessage(welcomeMsg);

            // Send on Enter key
            inputField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    send();
                }
            });

            // Focus input
            inputField.focus();
        });
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.post("/api/chat")
async def chat(chat_message: ChatMessage):
    """Send message to Jarvis MCP version (no auth in Part A)."""
    try:
        session_id = chat_message.session_id
        user_id = "web_user"  # Hardcoded for Part A

        # Create session if not exists
        try:
            session_service.create_session_sync(
                app_name="jarvis_mcp",
                user_id=user_id,
                session_id=session_id
            )
        except:
            pass  # Session already exists

        # Create runner
        runner = Runner(
            app_name="jarvis_mcp",
            agent=root_agent,
            session_service=session_service
        )

        # Prepare message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=chat_message.message)]
        )

        # Run agent and collect response
        response_text = ""
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            if event.content and event.content.parts and event.author != "user":
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        return {
            "success": True,
            "response": response_text if response_text else "I processed your request, but I don't have a response at the moment."
        }

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "version": "mcp",
        "port": 9990,
        "protocol": "Model Context Protocol",
        "authentication": "disabled (Part A)"
    }


@app.get("/api/info")
async def info():
    """Service information."""
    return {
        "service": "Jarvis MCP Web Interface",
        "version": "2.0.0-mcp",
        "port": 9990,
        "phase": "2A - No Authentication",
        "mcp_servers": {
            "tickets": "http://localhost:5011/mcp",
            "finops": "http://localhost:5012/mcp",
            "oxygen": "http://localhost:8012/mcp"
        },
        "note": "Existing web UI on port 9999 is UNCHANGED"
    }


if __name__ == "__main__":
    print("=" * 70)
    print(" Jarvis MCP Web Interface (Phase 2 - Part A: No Auth)")
    print("=" * 70)
    print()
    print("  Web UI: http://localhost:9990/")
    print("  API: http://localhost:9990/api/chat")
    print("  Health: http://localhost:9990/health")
    print("  Info: http://localhost:9990/api/info")
    print()
    print("  NOTE: No authentication in Part A (testing MCP only)")
    print("  NOTE: Existing web UI on port 9999 is UNCHANGED")
    print()
    print("  Connected to MCP servers:")
    print("    - Tickets: http://localhost:5011/mcp")
    print("    - FinOps: http://localhost:5012/mcp")
    print("    - Oxygen: http://localhost:8012/mcp")
    print("=" * 70)
    print()

    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment")
        print("   Please set it in your .env file")
        print()

    uvicorn.run(app, host="0.0.0.0", port=9990)
