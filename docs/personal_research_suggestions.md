## Agent Registry implementation

The cross-server queries not working is because the current system uses static sub_agents. To fix it:

  Option A: Quick Fix (Use Dynamic Router in main_mcp_auth.py)
  - Replace static sub_agents with dynamic routing
  - Takes ~30 minutes
  - Fixes the issue permanently


 
## Agent registry persistence 
 1. Medium Term (Phase 3)

  Integrate with ADK's session services:
  - Use DatabaseSessionService for conversation context
  - Separate database table for agent registry metadata
  - Link agents to sessions via agent_name field


