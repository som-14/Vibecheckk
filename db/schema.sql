-- This file defines the core schema, tables, constraints, and indexes for the VibeCheck application.

-- 1. Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('CREATOR', 'ADMIN'))
);

-- 2. TargetPersonas table
CREATE TABLE IF NOT EXISTS TargetPersonas (
    persona_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    min_age INT NOT NULL CHECK (min_age >= 13),
    max_age INT NOT NULL CHECK (max_age <= 99)
);

-- 3. Videos table
CREATE TABLE IF NOT EXISTS Videos (
    video_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES Users(user_id),
    persona_id INT REFERENCES TargetPersonas(persona_id),
    blob_url TEXT NOT NULL,
    caption TEXT,
    duration_seconds INT NOT NULL CHECK (duration_seconds BETWEEN 3 AND 180),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. ViralityPredictions table
CREATE TABLE IF NOT EXISTS ViralityPredictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL UNIQUE REFERENCES Videos(video_id) ON DELETE CASCADE,
    virality_score NUMERIC(5,2) NOT NULL CHECK (virality_score BETWEEN 0 AND 100),
    audience_fit_score NUMERIC(5,2) NOT NULL,
    classification VARCHAR(20) NOT NULL CHECK (classification IN ('VIRAL', 'AVERAGE', 'LOW')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. AgentCritiques table
CREATE TABLE IF NOT EXISTS AgentCritiques (
    critique_id BIGSERIAL PRIMARY KEY,
    prediction_id UUID NOT NULL REFERENCES ViralityPredictions(prediction_id) ON DELETE CASCADE,
    agent_role VARCHAR(100) NOT NULL,
    feedback_text TEXT NOT NULL,
    timestamp_marker NUMERIC(6,2),
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('CRITICAL', 'MEDIUM', 'INFO'))
);

-- 6. AuditLogs table
CREATE TABLE IF NOT EXISTS AuditLogs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES Users(user_id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    ip_address INET,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes

-- Index 1: Optimize querying videos uploaded by a user ordered by most recent
CREATE INDEX IF NOT EXISTS idx_videos_user_upload ON Videos(user_id, uploaded_at DESC);

-- Index 2: Covering index for filtering by virality classification and virality score while avoiding table lookups for video_id
CREATE INDEX IF NOT EXISTS idx_pred_class_score ON ViralityPredictions(classification, virality_score) INCLUDE (video_id);

-- Index 3: Index on Users(email).
-- NOTE: The column `email` is defined with a UNIQUE constraint, which automatically generates a backing unique B-tree index (users_email_key).
-- We create this named index `idx_users_email` explicitly as requested; it does not conflict with the existing constraint index in PostgreSQL.
CREATE INDEX IF NOT EXISTS idx_users_email ON Users(email);

