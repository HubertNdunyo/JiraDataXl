-- Migration: Add core business fields to jira_issues_v2 table
-- Date: 2025-01-09
-- Description: Adds essential business fields for JIRA synchronization

-- Add core business fields if they don't exist
ALTER TABLE jira_issues_v2 
ADD COLUMN IF NOT EXISTS ndpu_order_number VARCHAR(100),
ADD COLUMN IF NOT EXISTS ndpu_raw_photos INTEGER,
ADD COLUMN IF NOT EXISTS dropbox_raw_link TEXT,
ADD COLUMN IF NOT EXISTS dropbox_edited_link TEXT,
ADD COLUMN IF NOT EXISTS same_day_delivery VARCHAR(50),
ADD COLUMN IF NOT EXISTS escalated_editing VARCHAR(50),
ADD COLUMN IF NOT EXISTS edited_media_revision_notes TEXT,
ADD COLUMN IF NOT EXISTS ndpu_editing_team VARCHAR(255),
ADD COLUMN IF NOT EXISTS scheduled TIMESTAMP,
ADD COLUMN IF NOT EXISTS acknowledged TIMESTAMP,
ADD COLUMN IF NOT EXISTS at_listing TIMESTAMP,
ADD COLUMN IF NOT EXISTS shoot_complete TIMESTAMP,
ADD COLUMN IF NOT EXISTS uploaded TIMESTAMP,
ADD COLUMN IF NOT EXISTS edit_start TIMESTAMP,
ADD COLUMN IF NOT EXISTS final_review TIMESTAMP,
ADD COLUMN IF NOT EXISTS closed TIMESTAMP,
ADD COLUMN IF NOT EXISTS ndpu_service VARCHAR(255),
ADD COLUMN IF NOT EXISTS location_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS ndpu_client_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS ndpu_client_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS ndpu_comments TEXT,
ADD COLUMN IF NOT EXISTS ndpu_editor_notes TEXT,
ADD COLUMN IF NOT EXISTS ndpu_access_instructions TEXT,
ADD COLUMN IF NOT EXISTS ndpu_special_instructions TEXT,
ADD COLUMN IF NOT EXISTS ndpu_listing_address TEXT;

-- Create indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_ndpu_order_number 
    ON jira_issues_v2(ndpu_order_number) 
    WHERE ndpu_order_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_ndpu_client_email 
    ON jira_issues_v2(ndpu_client_email) 
    WHERE ndpu_client_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_shoot_complete 
    ON jira_issues_v2(shoot_complete) 
    WHERE shoot_complete IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_final_review 
    ON jira_issues_v2(final_review) 
    WHERE final_review IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_ndpu_service 
    ON jira_issues_v2(ndpu_service) 
    WHERE ndpu_service IS NOT NULL;

-- Add comments to document field purposes
COMMENT ON COLUMN jira_issues_v2.ndpu_order_number IS 'NDPU Order Number - unique identifier for orders';
COMMENT ON COLUMN jira_issues_v2.ndpu_raw_photos IS 'Number of raw photos in the order';
COMMENT ON COLUMN jira_issues_v2.dropbox_raw_link IS 'Link to raw media files in Dropbox';
COMMENT ON COLUMN jira_issues_v2.dropbox_edited_link IS 'Link to edited media files in Dropbox';
COMMENT ON COLUMN jira_issues_v2.same_day_delivery IS 'Flag for same day delivery requirement';
COMMENT ON COLUMN jira_issues_v2.escalated_editing IS 'Flag for escalated editing priority';
COMMENT ON COLUMN jira_issues_v2.edited_media_revision_notes IS 'Notes about media revisions';
COMMENT ON COLUMN jira_issues_v2.ndpu_editing_team IS 'Team assigned for editing';
COMMENT ON COLUMN jira_issues_v2.scheduled IS 'Timestamp when shoot was scheduled';
COMMENT ON COLUMN jira_issues_v2.acknowledged IS 'Timestamp when order was acknowledged';
COMMENT ON COLUMN jira_issues_v2.at_listing IS 'Timestamp when photographer arrived at listing';
COMMENT ON COLUMN jira_issues_v2.shoot_complete IS 'Timestamp when photography shoot was completed';
COMMENT ON COLUMN jira_issues_v2.uploaded IS 'Timestamp when media was uploaded';
COMMENT ON COLUMN jira_issues_v2.edit_start IS 'Timestamp when editing started';
COMMENT ON COLUMN jira_issues_v2.final_review IS 'Timestamp of final review';
COMMENT ON COLUMN jira_issues_v2.closed IS 'Timestamp when issue was closed';
COMMENT ON COLUMN jira_issues_v2.ndpu_service IS 'Type of service requested';
COMMENT ON COLUMN jira_issues_v2.location_name IS 'Location or region name';
COMMENT ON COLUMN jira_issues_v2.ndpu_client_name IS 'Client full name';
COMMENT ON COLUMN jira_issues_v2.ndpu_client_email IS 'Client email address';
COMMENT ON COLUMN jira_issues_v2.ndpu_comments IS 'General comments about the order';
COMMENT ON COLUMN jira_issues_v2.ndpu_editor_notes IS 'Notes for the editor';
COMMENT ON COLUMN jira_issues_v2.ndpu_access_instructions IS 'Property access instructions';
COMMENT ON COLUMN jira_issues_v2.ndpu_special_instructions IS 'Special instructions for the shoot';
COMMENT ON COLUMN jira_issues_v2.ndpu_listing_address IS 'Full property address';