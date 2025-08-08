-- Create jira_issues_v2 table
CREATE TABLE jira_issues_v2 (
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
    last_updated TIMESTAMP DEFAULT now(),
    location_name TEXT,
    ndpu_client_name TEXT,
    ndpu_client_email TEXT,
    ndpu_comments TEXT,
    ndpu_editor_notes TEXT,
    ndpu_access_instructions TEXT,
    ndpu_special_instructions TEXT
);

-- Create indexes for jira_issues_v2
CREATE INDEX idx_jira_issues_v2_location_name ON jira_issues_v2(location_name);
CREATE INDEX idx_jira_issues_v2_status ON jira_issues_v2(status);
CREATE INDEX ix_jira_issues_v2_project_name ON jira_issues_v2(project_name);

-- Create project_mappings_v2 table
CREATE TABLE project_mappings_v2 (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255) NOT NULL,
    location_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    auto_discovered BOOLEAN DEFAULT false,
    approved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    approved_by VARCHAR(255),
    metadata JSONB
);

-- Create indexes and constraints for project_mappings_v2
CREATE UNIQUE INDEX project_mappings_v2_project_key_key ON project_mappings_v2(project_key);
CREATE INDEX idx_project_mappings_v2_active ON project_mappings_v2(is_active);
CREATE INDEX idx_project_mappings_v2_key ON project_mappings_v2(project_key);

-- Create mapping_audit_log_v2 table
CREATE TABLE mapping_audit_log_v2 (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create update_log_v2 table
CREATE TABLE update_log_v2 (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255),
    last_update_time TIMESTAMP,
    status VARCHAR(50),
    duration NUMERIC,
    records_processed INTEGER,
    error_message TEXT
);

-- Create indexes for update_log_v2
CREATE INDEX idx_update_log_v2_project ON update_log_v2(project_key);
CREATE INDEX idx_update_log_v2_time ON update_log_v2(last_update_time);