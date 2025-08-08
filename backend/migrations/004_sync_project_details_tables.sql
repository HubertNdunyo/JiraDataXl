-- Migration: Create sync project details and performance metrics tables
-- Date: January 2025
-- Purpose: Phase 2 - Enhanced statistics and project-level tracking

-- Create sync_project_details table for tracking individual project sync results
CREATE TABLE IF NOT EXISTS jira_sync.sync_project_details (
    id SERIAL PRIMARY KEY,
    sync_run_id INTEGER REFERENCES jira_sync.sync_runs(id) ON DELETE CASCADE,
    project_key VARCHAR(255) NOT NULL,
    instance VARCHAR(50) NOT NULL CHECK (instance IN ('instance_1', 'instance_2')),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'skipped')),
    issues_processed INTEGER DEFAULT 0,
    issues_created INTEGER DEFAULT 0,
    issues_updated INTEGER DEFAULT 0,
    issues_failed INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for project details
CREATE INDEX idx_sync_project_sync_run ON jira_sync.sync_project_details(sync_run_id);
CREATE INDEX idx_sync_project_key ON jira_sync.sync_project_details(project_key);
CREATE INDEX idx_sync_project_status ON jira_sync.sync_project_details(status);

-- Create sync_performance_metrics table for tracking performance data
CREATE TABLE IF NOT EXISTS jira_sync.sync_performance_metrics (
    id SERIAL PRIMARY KEY,
    sync_run_id INTEGER REFERENCES jira_sync.sync_runs(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance metrics
CREATE INDEX idx_sync_metrics_sync_run ON jira_sync.sync_performance_metrics(sync_run_id);
CREATE INDEX idx_sync_metrics_name ON jira_sync.sync_performance_metrics(metric_name);
CREATE INDEX idx_sync_metrics_recorded ON jira_sync.sync_performance_metrics(recorded_at);

-- Add comments
COMMENT ON TABLE jira_sync.sync_project_details IS 'Tracks individual project sync results within a sync run';
COMMENT ON TABLE jira_sync.sync_performance_metrics IS 'Stores performance metrics for sync operations';