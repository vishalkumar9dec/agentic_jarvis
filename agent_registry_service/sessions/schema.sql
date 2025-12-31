-- =============================================================================
-- Agent Registry Service - Session Management Schema
-- =============================================================================
-- SQLite database schema for managing user sessions, conversation history,
-- agent invocations, and session context.
--
-- Features:
-- - Session tracking with metadata
-- - Complete conversation history
-- - Agent invocation logging
-- - Session context for continuity
-- - Performance indexes
-- - CASCADE deletes for data integrity
-- =============================================================================

-- Enable foreign key constraints (must be set for each connection)
PRAGMA foreign_keys = ON;

-- =============================================================================
-- Table: sessions
-- =============================================================================
-- Stores session metadata for each user interaction session.
-- A session represents a continuous conversation with the system.

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'expired')),
    metadata TEXT  -- JSON blob for additional session data
);

-- Indexes for sessions table
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- =============================================================================
-- Table: conversation_history
-- =============================================================================
-- Stores all messages in a conversation (user, assistant, system messages).
-- Enables full conversation replay and context reconstruction.

CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key with CASCADE delete
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Indexes for conversation_history table
CREATE INDEX IF NOT EXISTS idx_history_session ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON conversation_history(timestamp);

-- =============================================================================
-- Table: agent_invocations
-- =============================================================================
-- Tracks which agents were called during a session.
-- Includes query, response, success status, and performance metrics.

CREATE TABLE IF NOT EXISTS agent_invocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    success BOOLEAN NOT NULL DEFAULT 1,
    error_message TEXT,
    duration_ms INTEGER,  -- Execution duration in milliseconds
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key with CASCADE delete
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Indexes for agent_invocations table
CREATE INDEX IF NOT EXISTS idx_invocations_session ON agent_invocations(session_id);
CREATE INDEX IF NOT EXISTS idx_invocations_agent ON agent_invocations(agent_name);
CREATE INDEX IF NOT EXISTS idx_invocations_timestamp ON agent_invocations(timestamp);
CREATE INDEX IF NOT EXISTS idx_invocations_success ON agent_invocations(success);

-- =============================================================================
-- Table: session_context
-- =============================================================================
-- Tracks the last agent called and its interaction for context continuity.
-- Enables follow-up queries to understand the context (e.g., "show more details").

CREATE TABLE IF NOT EXISTS session_context (
    session_id TEXT PRIMARY KEY,
    last_agent_called TEXT,
    last_query TEXT,
    last_response TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key with CASCADE delete
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- =============================================================================
-- Triggers for automatic timestamp updates
-- =============================================================================

-- Update sessions.updated_at on any change
CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp
AFTER UPDATE ON sessions
FOR EACH ROW
BEGIN
    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
END;

-- Update session_context.updated_at on any change
CREATE TRIGGER IF NOT EXISTS update_context_timestamp
AFTER UPDATE ON session_context
FOR EACH ROW
BEGIN
    UPDATE session_context SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
END;

-- Update sessions.updated_at when new message added
CREATE TRIGGER IF NOT EXISTS update_session_on_message
AFTER INSERT ON conversation_history
FOR EACH ROW
BEGIN
    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
END;

-- Update sessions.updated_at when agent invoked
CREATE TRIGGER IF NOT EXISTS update_session_on_invocation
AFTER INSERT ON agent_invocations
FOR EACH ROW
BEGIN
    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
END;

-- =============================================================================
-- Views for common queries
-- =============================================================================

-- View: session_summary
-- Aggregated session information with counts
CREATE VIEW IF NOT EXISTS session_summary AS
SELECT
    s.session_id,
    s.user_id,
    s.created_at,
    s.updated_at,
    s.status,
    COUNT(DISTINCT ch.id) as message_count,
    COUNT(DISTINCT ai.id) as invocation_count,
    COUNT(DISTINCT ai.agent_name) as unique_agents,
    sc.last_agent_called
FROM sessions s
LEFT JOIN conversation_history ch ON s.session_id = ch.session_id
LEFT JOIN agent_invocations ai ON s.session_id = ai.session_id
LEFT JOIN session_context sc ON s.session_id = sc.session_id
GROUP BY s.session_id;

-- View: agent_performance
-- Agent performance metrics
CREATE VIEW IF NOT EXISTS agent_performance AS
SELECT
    agent_name,
    COUNT(*) as total_invocations,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_invocations,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_invocations,
    ROUND(AVG(duration_ms), 2) as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms
FROM agent_invocations
GROUP BY agent_name;

-- =============================================================================
-- Schema Version Tracking
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial schema with sessions, conversation_history, agent_invocations, and session_context');
