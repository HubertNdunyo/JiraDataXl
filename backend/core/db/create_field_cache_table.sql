-- Create table for caching JIRA field metadata
CREATE TABLE IF NOT EXISTS jira_sync.jira_field_cache (
    id SERIAL PRIMARY KEY,
    instance VARCHAR(50) NOT NULL,
    field_id VARCHAR(255) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(100),
    is_custom BOOLEAN DEFAULT false,
    is_array BOOLEAN DEFAULT false,
    schema_info JSONB,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(instance, field_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_field_cache_instance ON jira_sync.jira_field_cache(instance);
CREATE INDEX IF NOT EXISTS idx_field_cache_field_id ON jira_sync.jira_field_cache(field_id);
CREATE INDEX IF NOT EXISTS idx_field_cache_discovered_at ON jira_sync.jira_field_cache(discovered_at);

-- Add comment
COMMENT ON TABLE jira_sync.jira_field_cache IS 'Cache of JIRA field metadata for both instances';