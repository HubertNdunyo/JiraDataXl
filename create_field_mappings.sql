-- Create field_mappings_v2 table
CREATE TABLE field_mappings_v2 (
    id SERIAL PRIMARY KEY,
    jira_field_id VARCHAR(255) NOT NULL,  -- e.g., 'customfield_10501'
    display_name VARCHAR(255) NOT NULL,    -- e.g., 'Order Number'
    field_type VARCHAR(50) NOT NULL,       -- e.g., 'string', 'integer', 'boolean', 'timestamp'
    is_required BOOLEAN DEFAULT false,
    validation_rules JSONB,                -- Store validation rules as JSON
    default_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    project_key VARCHAR(255),              -- NULL for global fields, specific project key for project-specific fields
    metadata JSONB,                        -- Additional field metadata
    UNIQUE(jira_field_id, project_key)     -- Allow same field to have different mappings per project
);

-- Create index for common queries
CREATE INDEX idx_field_mappings_v2_active ON field_mappings_v2(is_active);
CREATE INDEX idx_field_mappings_v2_project ON field_mappings_v2(project_key);

-- Create audit log table for field mapping changes
CREATE TABLE field_mapping_audit_log_v2 (
    id SERIAL PRIMARY KEY,
    field_mapping_id INTEGER REFERENCES field_mappings_v2(id),
    action VARCHAR(50) NOT NULL,           -- 'CREATE', 'UPDATE', 'DELETE'
    old_value JSONB,
    new_value JSONB,
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial field mappings for existing fields
INSERT INTO field_mappings_v2 (
    jira_field_id, 
    display_name, 
    field_type, 
    is_required, 
    description
) VALUES 
('customfield_10501', 'Order Number', 'string', true, 'NDPU order number'),
('customfield_12602', 'Raw Photos Count', 'integer', false, 'Number of raw photos'),
('customfield_10713', 'Raw Dropbox Link', 'string', false, 'Link to raw photos in Dropbox'),
('customfield_10714', 'Edited Dropbox Link', 'string', false, 'Link to edited photos in Dropbox'),
('customfield_12661', 'Same Day Delivery', 'boolean', false, 'Whether this is a same-day delivery'),
('customfield_11712', 'Escalated Editing', 'boolean', false, 'Whether editing has been escalated'),
('customfield_10716', 'Revision Notes', 'string', false, 'Notes about media revisions'),
('customfield_12648', 'Editing Team', 'string', false, 'Team responsible for editing'),
('customfield_11104', 'Service Type', 'string', true, 'Type of service provided'),
('customfield_10600', 'Client Name', 'string', true, 'Name of the client'),
('customfield_10601', 'Client Email', 'string', true, 'Email of the client'),
('customfield_10612', 'Comments', 'string', false, 'General comments'),
('customfield_11601', 'Editor Notes', 'string', false, 'Notes from the editor');

-- Add function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to automatically update updated_at
CREATE TRIGGER update_field_mappings_updated_at
    BEFORE UPDATE ON field_mappings_v2
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE field_mappings_v2 IS 'Stores dynamic field mappings for JIRA fields';
COMMENT ON TABLE field_mapping_audit_log_v2 IS 'Tracks changes to field mappings';