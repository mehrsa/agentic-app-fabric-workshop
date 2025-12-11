-- ============================================
-- Multi-Agent Banking Chat Data Model - Table Creation
-- Drop tables in correct order (respecting foreign keys)
-- ============================================

-- Drop tables in reverse order of dependencies
IF OBJECT_ID('tool_usage', 'U') IS NOT NULL DROP TABLE tool_usage;
IF OBJECT_ID('chat_history', 'U') IS NOT NULL DROP TABLE chat_history;
IF OBJECT_ID('agent_traces', 'U') IS NOT NULL DROP TABLE agent_traces;
IF OBJECT_ID('chat_sessions', 'U') IS NOT NULL DROP TABLE chat_sessions;
IF OBJECT_ID('tool_definitions', 'U') IS NOT NULL DROP TABLE tool_definitions;
IF OBJECT_ID('agent_definitions', 'U') IS NOT NULL DROP TABLE agent_definitions;


-- ============================================
-- 1. Agent Definitions Table
-- Stores configuration for coordinator and specialist agents
-- ============================================
CREATE TABLE agent_definitions (
    agent_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description NVARCHAR(MAX),
    llm_config NVARCHAR(MAX) NOT NULL,  -- JSON stored as NVARCHAR
    prompt_template NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE()
);


-- ============================================
-- 2. Chat Sessions Table
-- Stores user chat sessions with multi-agent tracking
-- ============================================
CREATE TABLE chat_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    total_agents_used INT DEFAULT 0,
    agent_names_used NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    session_duration_ms INT DEFAULT 0
);


-- ============================================
-- 3. Agent Traces Table
-- Tracks agent routing and execution in multi-agent scenarios
-- ============================================
CREATE TABLE agent_traces (
    trace_step_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    trace_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    
    -- Multi-agent routing information
    from_agent VARCHAR(255),  -- Which coordinator routed this
    current_agent VARCHAR(255),       -- Which agent was selected
    
    -- Execution tracking
    step_order INT DEFAULT 1,
    execution_duration_ms INT,
    
    -- Result tracking
    success BIT DEFAULT 1,
    error_message NVARCHAR(MAX)
);


-- ============================================
-- 4. Tool Definitions Table
-- Stores tool configurations and agent associations
-- ============================================
CREATE TABLE tool_definitions (
    tool_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description NVARCHAR(MAX),
    input_schema NVARCHAR(MAX) NOT NULL,  -- JSON stored as NVARCHAR
    version VARCHAR(50) DEFAULT '1.0.0',
    is_active BIT DEFAULT 1,
    cost_per_call_cents INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);



-- ============================================
-- 5. Chat History Table
-- Stores all messages with multi-agent context
-- NOTE: session_id is NOT a foreign key (nullable, allows orphaned messages)
-- ============================================
CREATE TABLE chat_history (
    message_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,  -- NOT a foreign key, just a reference
    trace_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    
    -- Multi-agent tracking
    agent_id VARCHAR(255),
    agent_name VARCHAR(255),       -- Name of the agent
    routing_step INT,              -- Step in multi-agent flow
    
    -- Message content
    message_type VARCHAR(50) NOT NULL,  -- 'human', 'ai', 'system', 'tool_call', 'tool_result'
    content NVARCHAR(MAX),
    
    -- LLM metadata
    model_name VARCHAR(255),
    content_filter_results NVARCHAR(MAX),  -- JSON stored as NVARCHAR
    total_tokens INT,
    completion_tokens INT,
    prompt_tokens INT,
    
    -- Tool information
    tool_id VARCHAR(255),
    tool_name VARCHAR(255),
    tool_input NVARCHAR(MAX),      -- JSON stored as NVARCHAR
    tool_output NVARCHAR(MAX),     -- JSON stored as NVARCHAR
    tool_call_id VARCHAR(255),
    
    -- Response metadata
    finish_reason VARCHAR(255),
    response_time_ms INT,
    trace_end DATETIME2 DEFAULT GETDATE()
);


-- ============================================
-- 6. Tool Usage Table
-- Tracks tool execution with multi-agent context
-- ============================================
CREATE TABLE tool_usage (
    tool_call_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    trace_id VARCHAR(255),
    tool_id VARCHAR(255) NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    tool_input NVARCHAR(MAX) NOT NULL,  -- JSON stored as NVARCHAR
    tool_output NVARCHAR(MAX),          -- JSON stored as NVARCHAR
    tool_message NVARCHAR(MAX),
    status VARCHAR(50),
    
    -- Multi-agent context
    executing_agent VARCHAR(255),  -- Which agent executed this tool
    
    -- Performance tracking
    tokens_used INT
);


