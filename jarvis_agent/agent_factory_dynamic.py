"""
Dynamic Agent Factory with Agent Registry
Example of how to register agents and use dynamic routing.

This shows how to:
1. Register existing agents with capabilities
2. Use dynamic routing for 100+ agents
3. Auto-discover agents without manual routing rules
"""

from jarvis_agent.mcp_agents.agent_factory import (
    create_tickets_agent,
    create_finops_agent,
    create_oxygen_agent
)
from jarvis_agent.agent_registry import (
    AgentRegistry,
    AgentCapability,
    get_registry
)
from jarvis_agent.dynamic_router import create_router, TwoStageRouter


# =============================================================================
# Step 1: Register Agents with Explicit Capabilities
# =============================================================================

def register_agents_with_capabilities(registry: AgentRegistry) -> None:
    """
    Register all agents with their capabilities.

    This explicitly defines what each agent can do.
    For 100+ agents, you can:
    - Auto-extract from agent metadata (registry.register(agent))
    - Load from config files (YAML/JSON)
    - Use agent introspection
    """

    # Create agents
    tickets_agent = create_tickets_agent()
    finops_agent = create_finops_agent()
    oxygen_agent = create_oxygen_agent()

    # Register Tickets Agent
    tickets_caps = AgentCapability(
        domains=["tickets", "IT", "operations"],
        operations=["create", "read", "update", "list"],
        entities=["ticket", "request", "vpn", "gitlab", "ai_key", "access"],
        keywords={"ticket", "tickets", "operation", "request", "IT", "create", "status"},
        examples=[
            "show my tickets",
            "create a ticket for VPN access",
            "what's the status of ticket 12301?",
            "show all tickets"
        ],
        requires_auth=False,  # Has both public and authenticated tools
        priority=10
    )
    registry.register(tickets_agent, tickets_caps, tags={"production", "core"})

    # Register FinOps Agent
    finops_caps = AgentCapability(
        domains=["finops", "costs", "budget", "cloud"],
        operations=["read", "analyze", "breakdown"],
        entities=["cost", "budget", "cloud", "aws", "gcp", "azure", "spending"],
        keywords={"cost", "costs", "budget", "spending", "cloud", "aws", "gcp", "azure", "money", "expense"},
        examples=[
            "what are our total cloud costs?",
            "show me AWS spending",
            "give me a cost breakdown",
            "how much do we spend on GCP compute?"
        ],
        requires_auth=False,
        priority=10
    )
    registry.register(finops_agent, finops_caps, tags={"production", "core"})

    # Register Oxygen Agent
    oxygen_caps = AgentCapability(
        domains=["learning", "education", "oxygen", "courses"],
        operations=["read", "track", "monitor"],
        entities=["course", "exam", "learning", "training", "preference", "deadline"],
        keywords={"course", "courses", "exam", "exams", "learning", "training", "education", "study", "deadline", "preference"},
        examples=[
            "show my courses",
            "what exams do I have pending?",
            "show my learning preferences",
            "what's my learning progress?"
        ],
        requires_auth=False,  # Has both public and authenticated tools
        priority=10
    )
    registry.register(oxygen_agent, oxygen_caps, tags={"production", "core"})


# =============================================================================
# Step 2: Auto-Register Agents (Alternative Method)
# =============================================================================

def auto_register_agents(registry: AgentRegistry) -> None:
    """
    Auto-register agents without explicit capabilities.

    The registry will extract capabilities from agent metadata.
    This is faster for 100+ agents but less precise.
    """
    tickets_agent = create_tickets_agent()
    finops_agent = create_finops_agent()
    oxygen_agent = create_oxygen_agent()

    # Auto-register (capabilities extracted automatically)
    registry.register(tickets_agent)
    registry.register(finops_agent)
    registry.register(oxygen_agent)


# =============================================================================
# Step 3: Create Router and Use It
# =============================================================================

def create_dynamic_routing_system() -> tuple[AgentRegistry, TwoStageRouter]:
    """
    Create the complete dynamic routing system.

    Returns:
        Tuple of (registry, router) ready to use
    """
    # Create registry
    registry = get_registry()

    # Register agents (choose one method)
    register_agents_with_capabilities(registry)  # Explicit (recommended)
    # OR
    # auto_register_agents(registry)  # Auto-extract (faster, less precise)

    # Create router
    router = create_router(registry)

    return registry, router


# =============================================================================
# Step 4: Example Usage
# =============================================================================

def route_query_example():
    """Example of how to use the dynamic routing system."""

    # Setup
    registry, router = create_dynamic_routing_system()

    # Example queries
    test_queries = [
        "show my tickets",
        "show my tickets and courses",
        "what are my pending tickets, upcoming exams, and cloud costs?",
        "show all tickets",
        "what's our AWS spending?"
    ]

    print("=" * 70)
    print("DYNAMIC AGENT ROUTING EXAMPLES")
    print("=" * 70)
    print()

    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 70)

        # Route the query
        agents = router.route(query, require_all_matches=True)

        print(f"Selected Agents: {[agent.name for agent in agents]}")

        # Show explanation
        explanation = router.explain_routing(query)
        print(f"Reasoning:")
        print(f"  - Stage 1 candidates: {[c['name'] for c in explanation['stage1_candidates']]}")
        print(f"  - Stage 2 selected: {explanation['stage2_selected']}")
        print()


# =============================================================================
# Step 5: Integration with ADK Runner
# =============================================================================

async def handle_query_with_dynamic_routing(
    query: str,
    router: TwoStageRouter,
    session_context: dict
) -> str:
    """
    Handle a query using dynamic routing.

    This replaces the static sub_agents approach with dynamic routing.

    Args:
        query: User query
        router: TwoStageRouter instance
        session_context: Session context with auth token, etc.

    Returns:
        Combined response from all selected agents
    """
    # Stage 1 + 2: Discover relevant agents
    agents = router.route(query, require_all_matches=True)

    if not agents:
        return "I'm not sure which specialist can help with that. Can you rephrase?"

    # Call all selected agents
    responses = []
    for agent in agents:
        # Here you would call the agent with ADK Runner
        # For now, showing the structure
        # response = await agent.run(query, context=session_context)
        # responses.append((agent.name, response))
        pass

    # Combine responses
    if len(responses) == 1:
        return responses[0][1]
    else:
        # Multi-agent response formatting
        combined = []
        for agent_name, response in responses:
            combined.append(f"**{agent_name}:**\n{response}\n")
        return "\n".join(combined)


if __name__ == "__main__":
    # Run example
    route_query_example()
