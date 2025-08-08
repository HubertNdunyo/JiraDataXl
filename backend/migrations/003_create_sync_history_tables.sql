-- Migration: Create sync history tables
-- Date: January 2025
-- Purpose: Phase 1 MVP - Basic sync history persistence

-- Create sync_runs table for tracking sync operations
CREATE TABLE IF NOT EXISTS jira_sync.sync_runs (
    id SERIAL PRIMARY KEY,
    sync_id UUID UNIQUE NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'stopped')),
    sync_type VARCHAR(50) DEFAULT 'manual' CHECK (sync_type IN ('manual', 'scheduled', 'forced')),
    total_projects INTEGER DEFAULT 0,
    successful_projects INTEGER DEFAULT 0,
    failed_projects INTEGER DEFAULT 0,
    empty_projects INTEGER DEFAULT 0,
    total_issues INTEGER DEFAULT 0,
    error_message TEXT,
    initiated_by VARCHAR(255) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_sync_runs_started_at ON jira_sync.sync_runs(started_at DESC);
CREATE INDEX idx_sync_runs_status ON jira_sync.sync_runs(status);
CREATE INDEX idx_sync_runs_sync_id ON jira_sync.sync_runs(sync_id);

-- Add comment
COMMENT ON TABLE jira_sync.sync_runs IS 'Tracks all JIRA sync operations with basic statistics';