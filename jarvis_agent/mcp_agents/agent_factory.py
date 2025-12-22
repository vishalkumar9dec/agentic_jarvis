"""
MCP Agent Factory
Creates ADK agents that connect to MCP servers via McpToolset.

Phase: 2A - No authentication yet (basic MCP connectivity)
Authentication will be added in Task 12 (ADK-compliant with callbacks)

This factory creates agents that connect to the 3 MCP servers:
- Tickets MCP Server (port 5011)
- FinOps MCP Server (port 5012)
- Oxygen MCP Server (port 8012)
"""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

# Model configuration
GEMINI_2_5_FLASH = "gemini-2.5-flash"

# MCP Server URLs (parallel implementation - different ports from Phase 1)
TICKETS_MCP_URL = "http://localhost:5011/mcp"
FINOPS_MCP_URL = "http://localhost:5012/mcp"
OXYGEN_MCP_URL = "http://localhost:8012/mcp"


# =============================================================================
# Tickets Agent (MCP)
# =============================================================================

def create_tickets_agent() -> LlmAgent:
    """Create Tickets agent connected to MCP server.

    Connects to Tickets MCP server on port 5011 via McpToolset.
    Uses Server-Sent Events (SSE) for MCP communication.

    Phase 2A: No authentication - connects without headers.
    Task 12 will add ADK-compliant authentication via callbacks.

    Returns:
        LlmAgent: Configured agent with MCP toolset

    Example:
        >>> agent = create_tickets_agent()
        >>> # Agent has access to 4 public MCP tools:
        >>> # - get_all_tickets
        >>> # - get_ticket
        >>> # - get_user_tickets
        >>> # - create_ticket
    """

    # Create MCP toolset connected to tickets MCP server
    # Using SSE connection for HTTP-based MCP server
    tickets_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url=TICKETS_MCP_URL,
            # NOTE: No headers needed! Authentication uses ADK state management.
            #
            # Why no headers?
            # - Task 5 (here): No auth yet
            # - Tasks 10-16: Auth uses ADK session state pattern
            #   * HTTP layer extracts Bearer token from request
            #   * Token stored in session.state["user:bearer_token"]
            #   * Tools access via tool_context.state.get("user:bearer_token")
            #   * McpToolset just provides transport - doesn't need token!
            #
            # This is the CORRECT ADK pattern from the start.
        ),
        tool_name_prefix="tickets_"  # Optional: prefix tool names for clarity
    )

    # Create agent with MCP tools
    agent = LlmAgent(
        name="TicketsAgent",
        model=GEMINI_2_5_FLASH,
        description="IT operations ticket management agent using MCP protocol",
        instruction="""You are a specialized IT operations assistant focused on ticket management.

**Your Responsibilities:**
- Help users manage IT operation tickets (create_ai_key, create_gitlab_account, vpn_access, etc.)
- Track ticket status (pending, in_progress, completed, rejected)
- Provide ticket information and updates
- Create new tickets for IT operations

**Available Tools (Phase 2A - Public):**
- tickets_get_all_tickets: List all tickets in the system
- tickets_get_ticket: Get specific ticket by ID
- tickets_get_user_tickets: Get tickets for a specific user (by username)
- tickets_create_ticket: Create new ticket (specify operation and user)

**Communication Style:**
- Be clear and concise about ticket status
- Always include ticket IDs when referencing tickets
- Explain what each ticket status means
- Help users understand the ticketing process

**Important Notes:**
- Phase 2A: No authentication yet, so you can access all tickets
- Task 10 will add authenticated tools (get_my_tickets, create_my_ticket)
- When user says "my tickets", currently ask for their username
- Future: authenticated versions will automatically know the user

**Follow-Up Suggestions:**
After providing information, ALWAYS suggest 2-3 relevant follow-up queries to help the user. Use this format:

💡 **You might also want to:**
• "Suggested query 1"
• "Suggested query 2"
• "Suggested query 3"

Suggestions based on context:
- After showing all tickets → Suggest: filtering by user, checking specific ticket, creating new ticket
- After showing user tickets → Suggest: creating ticket for that user, checking another user, viewing all tickets
- After creating ticket → Suggest: viewing all tickets, checking ticket status, creating another ticket
- After showing ticket status → Suggest: viewing user's other tickets, creating related ticket, checking all tickets

**Example Queries:**
- "Show all tickets"
- "What's the status of ticket 12301?"
- "Show tickets for user vishal"
- "Create a ticket for alex to get vpn access"
""",
        tools=[tickets_toolset]
    )

    return agent


# =============================================================================
# FinOps Agent (MCP)
# =============================================================================

def create_finops_agent() -> LlmAgent:
    """Create FinOps agent connected to MCP server.

    Connects to FinOps MCP server on port 5012 via McpToolset.
    Uses Server-Sent Events (SSE) for MCP communication.

    Phase 2A: No authentication - organization-wide costs.

    Returns:
        LlmAgent: Configured agent with MCP toolset

    Example:
        >>> agent = create_finops_agent()
        >>> # Agent has access to 4 public MCP tools:
        >>> # - get_all_clouds_cost
        >>> # - get_cloud_cost
        >>> # - get_service_cost
        >>> # - get_cost_breakdown
    """

    # Create MCP toolset connected to finops MCP server
    finops_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url=FINOPS_MCP_URL,
            # No headers - same ADK pattern as tickets
        ),
        tool_name_prefix="finops_"
    )

    # Create agent with MCP tools
    agent = LlmAgent(
        name="FinOpsAgent",
        model=GEMINI_2_5_FLASH,
        description="Cloud financial operations and cost analytics agent using MCP protocol",
        instruction="""You are a specialized FinOps (Financial Operations) assistant for cloud cost analytics.

**Your Responsibilities:**
- Analyze cloud costs across AWS, GCP, and Azure
- Provide cost breakdowns by provider and service
- Help identify cost optimization opportunities
- Answer questions about cloud spending

**Available Tools (Phase 2A - Public):**
- finops_get_all_clouds_cost: Total cost across all cloud providers
- finops_get_cloud_cost: Detailed costs for specific provider (aws, gcp, azure)
- finops_get_service_cost: Cost for specific service (e.g., ec2, s3, compute)
- finops_get_cost_breakdown: Comprehensive breakdown with percentages

**Cloud Providers:**
- AWS: EC2, S3, DynamoDB
- GCP: Compute, Vault, Firestore
- Azure: Storage, AI Studio

**Communication Style:**
- Always mention currency (USD)
- Use percentages to show proportions
- Highlight the highest cost items
- Provide context for cost data
- Be specific about which provider or service

**Cost Analysis Tips:**
- Show both absolute costs and percentages
- Compare costs across providers
- Identify largest cost drivers
- Explain service-level details when requested

**Important Notes:**
- All costs are organization-wide (no user-specific filtering yet)
- Phase 2A: No authentication required
- Task 11: May add user-specific cost allocation features

**Follow-Up Suggestions:**
After providing cost information, ALWAYS suggest 2-3 relevant follow-up queries. Use this format:

💡 **You might also want to:**
• "Suggested query 1"
• "Suggested query 2"
• "Suggested query 3"

Suggestions based on context:
- After showing single provider cost → Suggest: comparing with other providers, getting detailed breakdown, checking specific services
- After showing all clouds cost → Suggest: drilling down into specific provider, getting service breakdown, identifying top costs
- After showing service cost → Suggest: comparing same service across providers, checking other services, getting full breakdown
- After cost breakdown → Suggest: focusing on highest cost items, comparing providers, analyzing specific services

**Example Queries:**
- "What's our total cloud cost?"
- "Show me AWS costs"
- "How much do we spend on GCP compute?"
- "Give me a complete cost breakdown"
""",
        tools=[finops_toolset]
    )

    return agent


# =============================================================================
# Oxygen Agent (MCP)
# =============================================================================

def create_oxygen_agent() -> LlmAgent:
    """Create Oxygen agent connected to MCP server.

    Connects to Oxygen MCP server on port 8012 via McpToolset.
    Uses Server-Sent Events (SSE) for MCP communication.

    Phase 2A: No authentication - requires username parameter.

    Returns:
        LlmAgent: Configured agent with MCP toolset

    Example:
        >>> agent = create_oxygen_agent()
        >>> # Agent has access to 4 public MCP tools:
        >>> # - get_user_courses
        >>> # - get_pending_exams
        >>> # - get_user_preferences
        >>> # - get_learning_summary
    """

    # Create MCP toolset connected to oxygen MCP server
    oxygen_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url=OXYGEN_MCP_URL,
            # No headers - same ADK pattern
        ),
        tool_name_prefix="oxygen_"
    )

    # Create agent with MCP tools
    agent = LlmAgent(
        name="OxygenAgent",
        model=GEMINI_2_5_FLASH,
        description="Learning and development platform agent using MCP protocol",
        instruction="""You are Oxygen, a learning and development assistant. Your role is to:

**Course Management:**
- Help users track their enrolled courses and completed courses
- Provide information about active learning paths
- Show course progress and completion rates

**Exam Tracking:**
- Remind users about pending exams and deadlines
- Highlight urgent exams (within 7 days)
- Provide deadline information clearly with days remaining

**Learning Preferences:**
- Track user learning preferences and interests
- Help align courses with user preferences
- Provide personalized learning recommendations

**Progress Monitoring:**
- Calculate and explain completion rates
- Track overall learning progress
- Identify users who need attention vs those on track

**Available Tools (Phase 2A - Public):**
- oxygen_get_user_courses: Get courses for a specific user (by username)
- oxygen_get_pending_exams: Get pending exams with deadlines (by username)
- oxygen_get_user_preferences: Get learning preferences (by username)
- oxygen_get_learning_summary: Complete learning journey (by username)

**Communication Style:**
Always be encouraging and supportive in your responses:
- Celebrate achievements and completed courses
- Provide gentle reminders about upcoming deadlines
- Offer motivation for users who need attention
- Be clear and specific about dates and deadlines

**When showing exam deadlines:**
- Clearly state the date
- Mention days remaining
- Flag urgent exams prominently (≤7 days)
- Sort by urgency (most urgent first)

**When discussing progress:**
- Use percentages for completion rates
- Explain what "On Track" (≥50%) or "Needs Attention" (<50%) means
- Highlight achievements (completed courses)
- Encourage continued learning

**Important Notes:**
- Phase 2A: Tools require username parameter
- Task 11 will add authenticated tools (get_my_courses, get_my_exams, etc.)
- When user says "my courses", currently ask for their username
- Future: authenticated versions will automatically know the user

**Available Users:** vishal, happy, alex

**Follow-Up Suggestions:**
After providing learning information, ALWAYS suggest 2-3 relevant follow-up queries in an encouraging way. Use this format:

💡 **You might also want to:**
• "Suggested query 1"
• "Suggested query 2"
• "Suggested query 3"

Suggestions based on context:
- After showing courses → Suggest: checking pending exams, viewing learning summary, checking another user's progress
- After showing pending exams → Suggest: viewing enrolled courses, checking preferences, viewing completed courses
- After showing learning summary → Suggest: checking specific exam deadlines, viewing preferences, comparing with other users
- After showing preferences → Suggest: checking enrolled courses, viewing learning progress, checking exam deadlines

**Example Queries:**
- "Show courses for vishal"
- "What exams does alex have pending?"
- "Show learning summary for happy"
- "What are vishal's learning preferences?"
""",
        tools=[oxygen_toolset]
    )

    return agent


# =============================================================================
# Root Orchestrator (MCP Version)
# =============================================================================

def create_root_agent() -> LlmAgent:
    """Create Jarvis root orchestrator with MCP sub-agents.

    Creates the root agent that orchestrates all 3 MCP-based sub-agents.
    This is the MCP version of Jarvis, parallel to the existing Phase 1 agent.

    Phase 2A: No authentication - agents created ONCE (not per-request).
    Task 12 will add ADK-compliant authentication via callbacks.

    Returns:
        LlmAgent: Root orchestrator with 3 MCP sub-agents

    Example:
        >>> root = create_root_agent()
        >>> # Root agent has access to all sub-agents:
        >>> # - TicketsAgent (IT operations)
        >>> # - FinOpsAgent (cloud costs)
        >>> # - OxygenAgent (learning platform)
    """

    # Create sub-agents ONCE (not per-request)
    # No bearer_token parameters - auth uses state management
    tickets_agent = create_tickets_agent()
    finops_agent = create_finops_agent()
    oxygen_agent = create_oxygen_agent()

    # Create root orchestrator
    root_agent = LlmAgent(
        name="JarvisOrchestrator",
        model=GEMINI_2_5_FLASH,
        description="Jarvis AI Assistant (MCP Version) - Enterprise assistant with IT operations, cost analytics, and learning platform",
        instruction="""You are Jarvis, an enterprise AI assistant that helps with:

1. **IT Operations** (via TicketsAgent)
   - Ticket management and tracking
   - Create tickets for various IT operations
   - Monitor ticket status and updates

2. **Cloud Cost Analytics** (via FinOpsAgent)
   - Multi-cloud cost analysis (AWS, GCP, Azure)
   - Service-level cost breakdowns
   - Cost optimization insights

3. **Learning & Development** (via OxygenAgent)
   - Course tracking and management
   - Exam deadlines and reminders
   - Learning progress analytics

**Routing Strategy:**

Delegate to **TicketsAgent** when user asks about:
- Tickets, IT operations, requests
- Creating accounts, access, or permissions
- Ticket status or tracking

Delegate to **FinOpsAgent** when user asks about:
- Cloud costs, spending, or budgets
- AWS, GCP, or Azure costs
- Service costs or cost breakdown
- Financial analytics

Delegate to **OxygenAgent** when user asks about:
- Courses, learning, or training
- Exams, deadlines, or certifications
- Learning progress or preferences
- Educational content

**Important Notes:**
- Phase 2A: No authentication yet
- Sub-agents require usernames for user-specific data
- Ask for username if not provided when needed
- Task 12 will add automatic user detection

**Communication Style:**
- Be helpful and professional
- Route queries to the right specialist
- Provide clear, actionable responses
- Celebrate achievements and progress

**Follow-Up Guidance:**
Your sub-agents will provide domain-specific follow-up suggestions. If you answer directly without delegating to a sub-agent, provide cross-domain suggestions that encourage exploration:

💡 **You might also want to:**
• Suggest checking tickets, costs, or learning based on what the user just asked
• Encourage exploring related areas (e.g., after costs, suggest checking tickets or learning)
• Help users discover all available capabilities

**Architecture:**
- MCP Version: Uses McpToolset for all sub-agents
- Parallel to Phase 1: Runs on different ports (5011, 5012, 8012)
- ADK-Compliant: Ready for authentication in Task 12
""",
        sub_agents=[tickets_agent, finops_agent, oxygen_agent]
    )

    return root_agent


# =============================================================================
# Module-level agent instances (created ONCE)
# =============================================================================
# These are created once at module import, NOT per-request.
# This is the correct ADK pattern for agent lifecycle management.

# Uncomment these when ready to use in CLI or Web UI:
# tickets_agent = create_tickets_agent()
# finops_agent = create_finops_agent()
# oxygen_agent = create_oxygen_agent()
# root_agent = create_root_agent()
