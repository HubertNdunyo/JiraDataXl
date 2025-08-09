-- PostgreSQL initialization script for JIRA Sync Dashboard
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Create main issues table
CREATE TABLE IF NOT EXISTS jira_issues_v2 (
    issue_key VARCHAR(255) PRIMARY KEY,
    summary TEXT,
    status VARCHAR(255),
    ndpu_order_number VARCHAR(255),
    ndpu_raw_photos INTEGER,
    dropbox_raw_link TEXT,
    dropbox_edited_link TEXT,
    same_day_delivery BOOLEAN,
    escalated_editing BOOLEAN,
    edited_media_revision_notes TEXT,
    ndpu_editing_team VARCHAR(255),
    scheduled TIMESTAMP,
    acknowledged TIMESTAMP,
    at_listing TIMESTAMP,
    shoot_complete TIMESTAMP,
    uploaded TIMESTAMP,
    edit_start TIMESTAMP,
    final_review TIMESTAMP,
    closed TIMESTAMP,
    ndpu_service VARCHAR(255),
    project_name TEXT,
    location_name TEXT,
    ndpu_client_name TEXT,
    ndpu_client_email TEXT,
    ndpu_listing_address TEXT,
    ndpu_comments TEXT,
    ndpu_editor_notes TEXT,
    ndpu_access_instructions TEXT,
    ndpu_special_instructions TEXT,
    last_updated TIMESTAMP DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_location_name 
ON jira_issues_v2(location_name);

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_project 
ON jira_issues_v2(project_name);

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_status 
ON jira_issues_v2(status);

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_last_updated 
ON jira_issues_v2(last_updated);

-- Create sync history table
CREATE TABLE IF NOT EXISTS sync_history (
    id SERIAL PRIMARY KEY,
    sync_id VARCHAR(255) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    total_issues INTEGER DEFAULT 0,
    issues_created INTEGER DEFAULT 0,
    issues_updated INTEGER DEFAULT 0,
    issues_failed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_type VARCHAR(50) DEFAULT 'manual',
    triggered_by VARCHAR(100),
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on sync history
CREATE INDEX IF NOT EXISTS idx_sync_history_start_time 
ON sync_history(start_time DESC);

CREATE INDEX IF NOT EXISTS idx_sync_history_status 
ON sync_history(status);

-- Create sync history details table
CREATE TABLE IF NOT EXISTS sync_history_details (
    id SERIAL PRIMARY KEY,
    sync_id VARCHAR(255) NOT NULL,
    issue_key VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sync_id) REFERENCES sync_history(sync_id) ON DELETE CASCADE
);

-- Create index on sync history details
CREATE INDEX IF NOT EXISTS idx_sync_history_details_sync_id 
ON sync_history_details(sync_id);

CREATE INDEX IF NOT EXISTS idx_sync_history_details_issue_key 
ON sync_history_details(issue_key);

-- Create project details table
CREATE TABLE IF NOT EXISTS sync_project_details (
    id SERIAL PRIMARY KEY,
    sync_id VARCHAR(255) NOT NULL,
    project_key VARCHAR(255) NOT NULL,
    project_name VARCHAR(255),
    issues_synced INTEGER DEFAULT 0,
    issues_created INTEGER DEFAULT 0,
    issues_updated INTEGER DEFAULT 0,
    issues_failed INTEGER DEFAULT 0,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sync_id) REFERENCES sync_history(sync_id) ON DELETE CASCADE
);

-- Create index on project details
CREATE INDEX IF NOT EXISTS idx_sync_project_details_sync_id 
ON sync_project_details(sync_id);

CREATE INDEX IF NOT EXISTS idx_sync_project_details_project_key 
ON sync_project_details(project_key);

-- Create field mappings table
CREATE TABLE IF NOT EXISTS field_mappings (
    id SERIAL PRIMARY KEY,
    jira_field_id VARCHAR(255) NOT NULL,
    jira_field_name VARCHAR(255) NOT NULL,
    db_column_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    is_custom BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    instance VARCHAR(50) DEFAULT 'instance_1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(jira_field_id, instance)
);

-- Create index on field mappings
CREATE INDEX IF NOT EXISTS idx_field_mappings_jira_field_id 
ON field_mappings(jira_field_id);

CREATE INDEX IF NOT EXISTS idx_field_mappings_instance 
ON field_mappings(instance);

-- Create configuration table
CREATE TABLE IF NOT EXISTS sync_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO sync_config (config_key, config_value, config_type, description) 
VALUES 
    ('sync_enabled', 'true', 'boolean', 'Enable/disable automatic synchronization'),
    ('sync_interval_minutes', '2', 'integer', 'Interval between automatic syncs in minutes'),
    ('batch_size', '100', 'integer', 'Number of issues to process in each batch'),
    ('max_retries', '3', 'integer', 'Maximum number of retry attempts for failed operations'),
    ('timeout_seconds', '30', 'integer', 'Request timeout in seconds')
ON CONFLICT (config_key) DO NOTHING;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create index on audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
ON audit_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id 
ON audit_log(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_action 
ON audit_log(action);

-- Create field cache table for performance
CREATE TABLE IF NOT EXISTS field_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on field cache
CREATE INDEX IF NOT EXISTS idx_field_cache_key 
ON field_cache(cache_key);

CREATE INDEX IF NOT EXISTS idx_field_cache_expires 
ON field_cache(expires_at);

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
END $$;