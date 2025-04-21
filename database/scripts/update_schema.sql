-- Drop existing table
DROP TABLE IF EXISTS jira_issues_v2;

-- Recreate table with correct columns
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

-- Recreate indexes
CREATE INDEX idx_jira_issues_v2_location_name ON jira_issues_v2(location_name);
CREATE INDEX idx_jira_issues_v2_status ON jira_issues_v2(status);
CREATE INDEX idx_jira_issues_v2_project ON jira_issues_v2(project_name);