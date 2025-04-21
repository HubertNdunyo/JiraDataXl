# Database Schema Documentation

This document outlines the schema for all tables that need to be created in the new database (jira_data_pipeline).

## 1. jira_issues_v2

Primary table for storing JIRA issue data.

```sql
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
    ndpu_listing_address TEXT, -- Added for listing address
    ndpu_comments TEXT,
    ndpu_editor_notes TEXT
);

-- Indexes
CREATE INDEX idx_jira_issues_v2_location_name ON jira_issues_v2(location_name);
CREATE INDEX idx_jira_issues_v2_status ON jira_issues_v2(status);
CREATE INDEX ix_jira_issues_v2_project_name ON jira_issues_v2(project_name);
```

## 2. project_mappings_v2

Stores project mapping information.

```sql
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

-- Indexes and Constraints
CREATE UNIQUE INDEX project_mappings_v2_project_key_key ON project_mappings_v2(project_key);
CREATE INDEX idx_project_mappings_v2_active ON project_mappings_v2(is_active);
CREATE INDEX idx_project_mappings_v2_key ON project_mappings_v2(project_key);
```

## 3. mapping_audit_log_v2

Tracks changes to project mappings.

```sql
CREATE TABLE mapping_audit_log_v2 (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. update_log_v2

Logs update operations.

```sql
CREATE TABLE update_log_v2 (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255),
    last_update_time TIMESTAMP,
    status VARCHAR(50),
    duration NUMERIC,
    records_processed INTEGER,
    error_message TEXT
);

-- Indexes
CREATE INDEX idx_update_log_v2_project ON update_log_v2(project_key);
CREATE INDEX idx_update_log_v2_time ON update_log_v2(last_update_time);
```

## Notes

1. All tables use the 'heap' access method
2. Timestamps are stored without time zone
3. The jira_issues_v2 table will be the main table for storing JIRA issue data
4. All tables have '_v2' suffix to differentiate them from the original tables
   
These schemas match the current production database structure but with '_v2' suffix added to all table names. They should be created in the new database (jira_data_pipeline) before data migration.