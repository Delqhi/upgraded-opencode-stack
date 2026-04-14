-- Supabase Schema for A2A Team Structure v5
-- Generated: 2026-04-14
-- This schema supports the new team-based agent organization

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    manager TEXT NOT NULL,
    description TEXT,
    primary_model TEXT NOT NULL,
    fallback_models TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents table (updated for team structure)
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    team_id UUID REFERENCES teams(id),
    type TEXT NOT NULL,
    description TEXT,
    primary_model TEXT NOT NULL,
    fallback_models TEXT[],
    capabilities TEXT[],
    status TEXT DEFAULT 'active',
    health_endpoint TEXT DEFAULT '/health',
    card_endpoint TEXT DEFAULT '/.well-known/agent-card.json',
    a2a_endpoint TEXT DEFAULT '/a2a/v1',
    hf_space TEXT,
    hf_account TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Work items table
CREATE TABLE IF NOT EXISTS work_items (
    id TEXT PRIMARY KEY,
    team TEXT NOT NULL,
    source TEXT,
    priority TEXT DEFAULT 'medium',
    type TEXT,
    description TEXT,
    status TEXT DEFAULT 'queued',
    assigned_agent TEXT,
    github_issue_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Agent health logs
CREATE TABLE IF NOT EXISTS agent_health_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- Token pool (for HF VM agents)
CREATE TABLE IF NOT EXISTS openai_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    token TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    rate_limited BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fleet knowledge vectors (for fleet memory)
CREATE TABLE IF NOT EXISTS fleet_knowledge_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agents_team ON agents(team_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_work_items_team ON work_items(team);
CREATE INDEX IF NOT EXISTS idx_work_items_status ON work_items(status);
CREATE INDEX IF NOT EXISTS idx_health_logs_agent ON agent_health_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_health_logs_time ON agent_health_logs(checked_at);
