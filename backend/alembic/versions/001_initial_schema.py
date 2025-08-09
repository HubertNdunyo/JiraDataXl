"""Initial schema migration

Revision ID: 001
Revises: 
Create Date: 2025-08-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create jira_issues_v2 table
    op.create_table('jira_issues_v2',
        sa.Column('issue_key', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('status', sa.String(255)),
        sa.Column('ndpu_order_number', sa.String(255)),
        sa.Column('ndpu_raw_photos', sa.Integer()),
        sa.Column('dropbox_raw_link', sa.Text()),
        sa.Column('dropbox_edited_link', sa.Text()),
        sa.Column('same_day_delivery', sa.Boolean()),
        sa.Column('escalated_editing', sa.Boolean()),
        sa.Column('edited_media_revision_notes', sa.Text()),
        sa.Column('ndpu_editing_team', sa.String(255)),
        sa.Column('scheduled', sa.TIMESTAMP()),
        sa.Column('acknowledged', sa.TIMESTAMP()),
        sa.Column('at_listing', sa.TIMESTAMP()),
        sa.Column('shoot_complete', sa.TIMESTAMP()),
        sa.Column('uploaded', sa.TIMESTAMP()),
        sa.Column('edit_start', sa.TIMESTAMP()),
        sa.Column('final_review', sa.TIMESTAMP()),
        sa.Column('closed', sa.TIMESTAMP()),
        sa.Column('ndpu_service', sa.String(255)),
        sa.Column('project_name', sa.Text()),
        sa.Column('location_name', sa.Text()),
        sa.Column('ndpu_client_name', sa.Text()),
        sa.Column('ndpu_client_email', sa.Text()),
        sa.Column('ndpu_listing_address', sa.Text()),
        sa.Column('ndpu_comments', sa.Text()),
        sa.Column('ndpu_editor_notes', sa.Text()),
        sa.Column('ndpu_access_instructions', sa.Text()),
        sa.Column('ndpu_special_instructions', sa.Text()),
        sa.Column('last_updated', sa.TIMESTAMP(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('issue_key')
    )
    
    # Create indexes for jira_issues_v2
    op.create_index('idx_jira_issues_v2_location_name', 'jira_issues_v2', ['location_name'])
    op.create_index('idx_jira_issues_v2_project', 'jira_issues_v2', ['project_name'])
    op.create_index('idx_jira_issues_v2_status', 'jira_issues_v2', ['status'])
    op.create_index('idx_jira_issues_v2_last_updated', 'jira_issues_v2', ['last_updated'])
    
    # Create sync_history table
    op.create_table('sync_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_id', sa.String(255), nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP()),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('total_issues', sa.Integer(), server_default='0'),
        sa.Column('issues_created', sa.Integer(), server_default='0'),
        sa.Column('issues_updated', sa.Integer(), server_default='0'),
        sa.Column('issues_failed', sa.Integer(), server_default='0'),
        sa.Column('error_message', sa.Text()),
        sa.Column('sync_type', sa.String(50), server_default='manual'),
        sa.Column('triggered_by', sa.String(100)),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sync_id')
    )
    
    # Create indexes for sync_history
    op.create_index('idx_sync_history_start_time', 'sync_history', ['start_time'])
    op.create_index('idx_sync_history_status', 'sync_history', ['status'])
    
    # Create sync_history_details table
    op.create_table('sync_history_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_id', sa.String(255), nullable=False),
        sa.Column('issue_key', sa.String(255), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['sync_id'], ['sync_history.sync_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for sync_history_details
    op.create_index('idx_sync_history_details_sync_id', 'sync_history_details', ['sync_id'])
    op.create_index('idx_sync_history_details_issue_key', 'sync_history_details', ['issue_key'])
    
    # Create sync_project_details table
    op.create_table('sync_project_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_id', sa.String(255), nullable=False),
        sa.Column('project_key', sa.String(255), nullable=False),
        sa.Column('project_name', sa.String(255)),
        sa.Column('issues_synced', sa.Integer(), server_default='0'),
        sa.Column('issues_created', sa.Integer(), server_default='0'),
        sa.Column('issues_updated', sa.Integer(), server_default='0'),
        sa.Column('issues_failed', sa.Integer(), server_default='0'),
        sa.Column('sync_time', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['sync_id'], ['sync_history.sync_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for sync_project_details
    op.create_index('idx_sync_project_details_sync_id', 'sync_project_details', ['sync_id'])
    op.create_index('idx_sync_project_details_project_key', 'sync_project_details', ['project_key'])
    
    # Create field_mappings table
    op.create_table('field_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jira_field_id', sa.String(255), nullable=False),
        sa.Column('jira_field_name', sa.String(255), nullable=False),
        sa.Column('db_column_name', sa.String(255), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False),
        sa.Column('is_custom', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('instance', sa.String(50), server_default='instance_1'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jira_field_id', 'instance')
    )
    
    # Create indexes for field_mappings
    op.create_index('idx_field_mappings_jira_field_id', 'field_mappings', ['jira_field_id'])
    op.create_index('idx_field_mappings_instance', 'field_mappings', ['instance'])
    
    # Create sync_config table
    op.create_table('sync_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(255), nullable=False),
        sa.Column('config_value', sa.Text()),
        sa.Column('config_type', sa.String(50), server_default='string'),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    
    # Insert default configuration
    op.execute("""
        INSERT INTO sync_config (config_key, config_value, config_type, description) 
        VALUES 
            ('sync_enabled', 'true', 'boolean', 'Enable/disable automatic synchronization'),
            ('sync_interval_minutes', '2', 'integer', 'Interval between automatic syncs in minutes'),
            ('batch_size', '100', 'integer', 'Number of issues to process in each batch'),
            ('max_retries', '3', 'integer', 'Maximum number of retry attempts for failed operations'),
            ('timeout_seconds', '30', 'integer', 'Request timeout in seconds')
        ON CONFLICT (config_key) DO NOTHING
    """)
    
    # Create audit_log table
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.String(255)),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('details', postgresql.JSONB()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_log
    op.create_index('idx_audit_log_timestamp', 'audit_log', ['timestamp'])
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])
    
    # Create field_cache table
    op.create_table('field_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('cache_value', postgresql.JSONB()),
        sa.Column('expires_at', sa.TIMESTAMP()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    
    # Create indexes for field_cache
    op.create_index('idx_field_cache_key', 'field_cache', ['cache_key'])
    op.create_index('idx_field_cache_expires', 'field_cache', ['expires_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('field_cache')
    op.drop_table('audit_log')
    op.drop_table('sync_config')
    op.drop_table('field_mappings')
    op.drop_table('sync_project_details')
    op.drop_table('sync_history_details')
    op.drop_table('sync_history')
    op.drop_table('jira_issues_v2')