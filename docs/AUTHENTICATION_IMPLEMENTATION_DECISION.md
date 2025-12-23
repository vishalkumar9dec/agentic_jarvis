# Authentication Implementation Decision for MCP Tools

**Date**: 2025-12-23
**Phase**: Phase 2B - Task 13
**Status**: ✅ Implemented and Verified
**Implementation Date**: 2025-12-23

## Executive Summary

This document defines the official authentication architecture for passing JWT bearer tokens from the ADK App layer to MCP tools. After testing and validation, we've identified that **McpToolset's `header_provider` parameter** is the correct ADK-compliant approach.

---

## ✅ Final Working Solution

**Implementation Status**: Successfully tested and verified on 2025-12-23

### Critical Discovery: EventActions with state_delta

The blocking issue was how to properly store the bearer token in session state so it's accessible to `header_provider`. The solution came from [ADK Loop Agents documentation](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/#full-example-iterative-document-improvement):

**Key Pattern**: Use `EventActions` with `state_delta` to update session state

```python
from google.adk.events import Event, EventActions
from google.genai import types as genai_types
import asyncio

# Create event with state_delta to update session state
state_update_event = Event(
    content=genai_types.Content(
        role="user",
        parts=[genai_types.Part(text="[Auth] Session initialized")]
    ),
    author="system",
    actions=EventActions(  # ← NOT Actions, must be EventActions
        state_delta={
            # Keys WITHOUT prefix → session state (accessible via context.session.state)
            "bearer_token": bearer_token,  # ← NO "user:" prefix
            "username": user_info['username'],
            "role": user_info['role'],
            "user_id": user_info['user_id']
        }
    )
)

# Append event (MUST use async)
asyncio.run(session_service.append_event(session, state_update_event))
```

**Critical Insights**:

1. **State Prefixes Matter** (from ADK source: `_session_util.extract_state_delta`):
   - Keys with NO prefix → session state (accessible via `context.session.state`)
   - Keys with `user:` prefix → user state (NOT accessible in session state)
   - Keys with `app:` prefix → app state

2. **EventActions vs Actions**: Must use `EventActions` from `google.adk.events`, not `Actions`

3. **Async Requirement**: `append_event` is async and must be called with `asyncio.run()`

4. **Header Provider Access**: The header_provider receives a `context` parameter with access to `context.session.state.get("bearer_token")`

### FastMCP Header Extraction Solution

**Discovery**: FastMCP provides `get_http_headers()` function from `fastmcp.server.dependencies`

```python
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

@mcp.tool()
def get_my_tickets() -> List[Dict]:
    """Get tickets for the authenticated user via HTTP Authorization header."""

    # Extract bearer token from HTTP Authorization header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")

    if not auth_header or not auth_header.startswith("Bearer "):
        return {"error": "Authentication required", "status": 401}

    bearer_token = auth_header[7:]  # Remove "Bearer " prefix

    # Validate token
    payload = verify_jwt_token(bearer_token)
    if not payload:
        return {"error": "Invalid or expired token", "status": 401}

    current_user = payload.get("username")

    # Return user-specific tickets
    return [t for t in TICKETS_DB if t['user'].lower() == current_user.lower()]
```

### Verification Results

**Test Date**: 2025-12-23

✅ **Login Flow**: User authentication via JWT working correctly
✅ **Session State**: Bearer token successfully stored in `context.session.state`
✅ **Header Injection**: Authorization header properly injected into MCP HTTP requests
✅ **Token Validation**: MCP servers correctly extract and validate JWT tokens
✅ **User Isolation**: Authenticated users only see their own data
  - User `vishal` sees tickets #12301, #12303 (his tickets only)
  - User `alex` would see tickets #12302, #12304 (his tickets only)

**Evidence**: See test outputs in `/tmp/AUTHENTICATION_SUCCESS_FINAL.txt`

---

## Problem Statement

**Challenge**: How do we pass the authenticated user's bearer token from the ADK session state (`session.state["user:bearer_token"]`) to MCP tools running on remote HTTP servers?

**Requirements**:
1. Agents are created ONCE at startup (not per-session) - per ADK best practices
2. Sessions are per-user with different bearer tokens
3. MCP tools need the bearer token to validate user identity
4. Solution must be ADK-compliant and documented

---

## Tested Approaches & Results

### ❌ Approach 1: ToolContext Parameter (FAILED)

**Attempted Pattern**:
```python
from google.adk.tools import ToolContext

@mcp.tool()
def get_my_tickets(tool_context: ToolContext) -> List[Dict]:
    bearer_token = tool_context.state.get("user:bearer_token")
    # ... validate and use token
```

**Why It Failed**:
```
pydantic.errors.PydanticSchemaGenerationError: Unable to generate pydantic-core
schema for <class 'google.adk.tools.tool_context.ToolContext'>
```

**Root Cause**: FastMCP uses Pydantic to validate tool parameters. `ToolContext` is not a Pydantic-serializable type, so it cannot be passed over HTTP to remote MCP servers.

**Reference**: Tested in Task 12, error occurred during MCP server startup.

---

### ❌ Approach 2: bearer_token as Tool Parameter (INCOMPLETE)

**Attempted Pattern**:
```python
@mcp.tool()
def get_my_tickets(bearer_token: str = "") -> List[Dict]:
    # ... validate token
```

**Issue**: While this syntax works, there's no automatic mechanism to populate the `bearer_token` parameter from session state. McpToolset doesn't know about session state - it just makes HTTP calls.

**Missing Piece**: How does the token get from `session.state["user:bearer_token"]` to the tool parameter?

---

### ✅ Approach 3: McpToolset header_provider (CORRECT)

**Official ADK Pattern**:

McpToolset has a `header_provider` parameter that allows injection of HTTP headers for each MCP request:

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

toolset = McpToolset(
    connection_params=SseConnectionParams(url="http://localhost:5011/mcp"),
    header_provider=callable_that_returns_headers,
    tool_name_prefix="tickets_"
)
```

**Discovery**: During code inspection of McpToolset parameters (line 59 in agent_factory.py), we found the `header_provider` parameter exists but was not documented in our implementation.

**How It Works**:
1. `header_provider` is a callable that returns `Dict[str, str]` (HTTP headers)
2. McpToolset invokes this callable before each MCP tool request
3. Headers are included in the HTTP request to the MCP server
4. MCP server extracts the `Authorization: Bearer <token>` header
5. Token is validated and used for user identification

---

## Proposed Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI / Web UI                            │
│  1. User logs in → receives bearer_token                    │
│  2. Token stored in session.state["user:bearer_token"]      │
│  3. Before agent call: set_bearer_token(token) ← Context    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     ADK App Layer                            │
│  - App.run(session_id, new_message)                         │
│  - Routes to appropriate agent                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  McpToolset (per agent)                      │
│  - Created ONCE at startup                                  │
│  - header_provider=create_auth_header_provider()            │
│  - Before each HTTP call:                                   │
│    * Calls header_provider() → {"Authorization": "Bearer …"}│
│    * Injects headers into HTTP request                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ HTTP POST with Authorization header
┌─────────────────────────────────────────────────────────────┐
│                  MCP Server (FastMCP)                        │
│  - Receives HTTP request with Authorization header          │
│  - Extracts token from header                               │
│  - Passes to tool function (or validates first)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tool Function                         │
│  @mcp.tool()                                                │
│  def get_my_tickets(bearer_token: str):                     │
│      # Token already extracted from HTTP header             │
│      payload = verify_jwt_token(bearer_token)               │
│      return user_specific_data                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Context Management (`auth_context.py`)

**Purpose**: Maintain current bearer token across async boundaries using Python's `contextvars`.

**Why contextvars?**
- Thread-safe and async-safe
- Automatically propagates across async calls
- Isolated per execution context (different users don't interfere)

**Key Functions**:
```python
set_bearer_token(token: str)      # Called by CLI before agent.run()
get_bearer_token() -> str         # Called by header_provider
clear_bearer_token()              # Called after request completes
```

#### 2. Header Provider (`auth_context.py`)

**Purpose**: Callable that McpToolset invokes to get HTTP headers for each request.

```python
def create_auth_header_provider() -> callable:
    def header_provider() -> Dict[str, str]:
        token = get_bearer_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    return header_provider
```

**Why a factory function?**
- Each McpToolset instance gets its own header_provider
- The provider has closure over the context variables
- Clean separation of concerns

#### 3. Agent Factory Updates (`agent_factory.py`)

**Change**: Add `header_provider` parameter to all McpToolset instances.

**Before**:
```python
tickets_toolset = McpToolset(
    connection_params=SseConnectionParams(url=TICKETS_MCP_URL),
    tool_name_prefix="tickets_"
)
```

**After**:
```python
from jarvis_agent.mcp_agents.auth_context import create_auth_header_provider

tickets_toolset = McpToolset(
    connection_params=SseConnectionParams(url=TICKETS_MCP_URL),
    header_provider=create_auth_header_provider(),  # ← NEW
    tool_name_prefix="tickets_"
)
```

**Apply to**: Tickets, FinOps, Oxygen toolsets

#### 4. CLI Updates (`main_mcp_auth.py`)

**Change**: Set bearer token in context before calling agent.

**Before**:
```python
for event in app.run(user_id=user_id, session_id=session_id, new_message=new_message):
    # Process events
```

**After**:
```python
from jarvis_agent.mcp_agents.auth_context import set_bearer_token

# Set token in context before agent call
set_bearer_token(bearer_token)

for event in app.run(user_id=user_id, session_id=session_id, new_message=new_message):
    # Process events
```

#### 5. MCP Server Updates

**Change**: Extract bearer token from HTTP Authorization header instead of tool parameter.

**Current State** (from Task 12):
```python
@mcp.tool()
def get_my_tickets(bearer_token: str = "") -> List[Dict]:
    if not bearer_token:
        return {"error": "Authentication required"}
    # ... validate and use
```

**Proposed Change**:
MCP servers need to extract the token from the incoming HTTP request's Authorization header and pass it to the tool. This requires understanding FastMCP's request context handling.

**Options**:
- A) Keep parameter, but populate from request header at FastMCP layer
- B) Use FastMCP dependency injection to access request context
- C) Use middleware to extract and inject token

**Decision Needed**: Which FastMCP pattern should we use? (Requires FastMCP documentation review)

---

## Validation Against Official Documentation

### ADK Documentation References

**McpToolset header_provider**:
- Parameter exists in McpToolset signature (confirmed via inspection)
- Purpose: Inject HTTP headers dynamically for each MCP request
- Use case: Authentication, custom headers, rate limiting

**Agent Lifecycle**:
- ✅ Agents created once at startup (not per-request) - [ADK Best Practices]
- ✅ Session state per user - [InMemorySessionService documentation]
- ✅ Tools can be stateless and shared across sessions

**Session State Management**:
- ✅ `session.state` is a dict for storing session-specific data
- ✅ Common pattern: Store user identity, preferences, authentication tokens
- Reference: `InMemorySessionService` in ADK

### FastMCP Documentation References

**Tool Parameters**:
- ✅ Tool parameters must be Pydantic-serializable (JSON-compatible)
- ✅ HTTP-based MCP uses JSON-RPC over HTTP POST
- ✅ Headers are separate from tool parameters

**Request Context**:
- [ ] **TODO**: Verify how FastMCP provides access to HTTP request headers
- [ ] **TODO**: Document the pattern for extracting Authorization header

---

## Changes to Existing Documentation

### Files Requiring Updates

#### 1. `docs/AUTHENTICATION_FLOW.md`

**Current Content**: Shows using `ToolContext` in MCP tools (doesn't work)

**Required Changes**:
- Remove references to `ToolContext` in MCP tools
- Add section on `header_provider` pattern
- Update flow diagram to show HTTP Authorization header
- Add contextvars explanation

**Status**: ⚠️ NEEDS UPDATE

#### 2. `docs/MCP_CORRECT_IMPLEMENTATION.md`

**Current Content**: Shows BOTH `ToolContext` and `bearer_token` patterns (conflicting)

**Required Changes**:
- Remove `ToolContext` pattern entirely
- Standardize on `header_provider` + HTTP Authorization header
- Add code examples for all three layers (CLI, Agent Factory, MCP Server)
- Clarify that agents are created once, not per-session

**Status**: ⚠️ NEEDS UPDATE

#### 3. `jarvis_agent/mcp_agents/agent_factory.py`

**Current Content**: Comments mention "tools access via tool_context.state" (incorrect)

**Required Changes**:
- Update comments to reflect header_provider pattern
- Remove references to ToolContext
- Add clear explanation of authentication flow in comments

**Status**: ⚠️ NEEDS UPDATE (implementation in progress)

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Task 13) - ✅ COMPLETED
- [x] Create `auth_context.py` with contextvars pattern
- [x] Update `agent_factory.py` to use `header_provider`
- [x] Update `main_mcp_auth.py` to implement EventActions pattern
- [x] Implement session state storage using `state_delta` (without prefix)
- [x] Update tickets MCP server to extract token from HTTP headers using `get_http_headers()`
- [x] Test end-to-end authenticated flow - ✅ WORKING

### Phase 2: Documentation Updates - 🔄 IN PROGRESS
- [x] Update `AUTHENTICATION_IMPLEMENTATION_DECISION.md` with final solution
- [x] Create comprehensive test instructions (`TASK_13_TEST_INSTRUCTIONS.md`)
- [ ] Update `AUTHENTICATION_FLOW.md` (pending)
- [ ] Update `MCP_CORRECT_IMPLEMENTATION.md` (pending)
- [ ] Create migration guide for existing code (pending)

### Phase 3: Testing - ✅ COMPLETED (Tickets MCP Server)
- [x] Test public tools (no auth) - ✅ `get_all_tickets()` working
- [x] Test authenticated tools with valid token - ✅ `get_my_tickets()` working
- [x] Test authenticated tools without token - ✅ Returns 401 error gracefully
- [x] Test user isolation - ✅ Users only see their own tickets
- [x] Test authenticated ticket creation - ✅ `create_my_ticket()` working
- [ ] Test concurrent sessions with different users (manual test pending)

### Phase 4: Replication to Other MCP Servers - 🔜 NEXT
- [ ] Replicate authentication to Oxygen MCP Server (4 tools)
- [ ] Replicate authentication to FinOps MCP Server (if needed)
- [ ] Test all authenticated tools across all servers

---

## Open Questions

1. ~~**FastMCP Header Extraction**: What is the official FastMCP pattern for accessing HTTP request headers in tool functions?~~
   - ✅ **RESOLVED**: Use `get_http_headers()` from `fastmcp.server.dependencies`

2. ~~**Session State Storage**: How to properly store bearer token in session state?~~
   - ✅ **RESOLVED**: Use `EventActions` with `state_delta`, keys without prefix for session state

3. **Error Handling**: If header_provider fails, how should McpToolset behave?
   - **Current Implementation**: Returns empty dict, tools fail gracefully with 401
   - **Status**: Working as expected

4. **Token Refresh**: How do we handle token expiration during a long conversation?
   - **Status**: Phase 3 concern, tokens currently don't expire

5. **Callbacks Integration**: The `callbacks.py` module currently validates tokens. Should we:
   - Keep validation in callbacks (centralized) ← Current approach
   - Move validation to MCP servers (distributed) ← Also implemented for defense in depth
   - **Status**: Using both approaches for maximum security

---

## Recommendations

### ✅ Completed Actions (Task 13)

1. ✅ **Architecture Approved**: `header_provider` with EventActions pattern implemented
2. ✅ **FastMCP Pattern Identified**: Using `get_http_headers()` for header extraction
3. ✅ **Implementation Complete**: Tickets MCP Server fully authenticated
4. ✅ **Testing Verified**: User isolation and authentication working correctly

### Immediate Next Steps

1. **Replicate to Oxygen MCP Server**: Apply the same authentication pattern to Oxygen's 4 authenticated tools
2. **User Testing**: Follow test instructions in `TASK_13_TEST_INSTRUCTIONS.md`
3. **Update Remaining Documentation**: Update `AUTHENTICATION_FLOW.md` and `MCP_CORRECT_IMPLEMENTATION.md`

### Future Considerations (Phase 3)

- Token refresh mechanism (implement JWT expiration)
- Session timeout handling
- Multi-device session management
- Audit logging for authenticated tool calls
- Rate limiting per user

---

## Conclusion

The **`header_provider` pattern with EventActions** is the correct, ADK-compliant approach for authentication in MCP-based agents. This pattern has been **successfully implemented and verified**.

### What Makes This Work

- ✅ Respects ADK best practices (agents created once, Runner pattern)
- ✅ Uses official McpToolset parameters (`header_provider`)
- ✅ Proper session state management (`EventActions` with `state_delta`)
- ✅ Correct state key usage (no prefix for session state)
- ✅ FastMCP header extraction (`get_http_headers()`)
- ✅ Maintains session isolation (contextvars as fallback)
- ✅ Follows HTTP standards (Authorization: Bearer header)
- ✅ Keeps tools stateless and reusable

### Verification Evidence

**Authentication Flow**: ✅ Fully Working
- User logs in → receives JWT token
- Token stored in session state via EventActions
- Token injected into HTTP headers via header_provider
- MCP server extracts and validates token
- User-specific data returned

**User Isolation**: ✅ Confirmed
- User `vishal` sees only tickets #12301, #12303
- Public tools show all tickets correctly
- Authenticated tools enforce user-specific filtering

**Next Step**: Replicate this pattern to Oxygen MCP Server and complete Phase 2B authentication implementation.
