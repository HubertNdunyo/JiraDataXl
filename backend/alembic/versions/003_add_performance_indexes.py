"""Add indexes for performance

Revision ID: 003
Revises: 002
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes for better query performance
    # issue_key is already primary key (indexed by default)
    
    # Get connection to check existing indexes
    conn = op.get_bind()
    
    # Query to check if an index exists
    def index_exists(index_name):
        result = conn.execute(sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname = :name"
        ), {"name": index_name})
        return result.fetchone() is not None
    
    # Create indexes only if they don't exist
    if not index_exists('idx_jira_issues_v2_summary'):
        op.create_index('idx_jira_issues_v2_summary', 'jira_issues_v2', ['summary'])
    
    if not index_exists('idx_jira_issues_v2_ndpu_order_number'):
        op.create_index('idx_jira_issues_v2_ndpu_order_number', 'jira_issues_v2', ['ndpu_order_number'])
    
    if not index_exists('idx_jira_issues_v2_ndpu_listing_address'):
        op.create_index('idx_jira_issues_v2_ndpu_listing_address', 'jira_issues_v2', ['ndpu_listing_address'])
    
    if not index_exists('idx_jira_issues_v2_status'):
        op.create_index('idx_jira_issues_v2_status', 'jira_issues_v2', ['status'])
    
    if not index_exists('idx_jira_issues_v2_project_name'):
        op.create_index('idx_jira_issues_v2_project_name', 'jira_issues_v2', ['project_name'])
    
    if not index_exists('idx_jira_issues_v2_last_updated'):
        op.create_index('idx_jira_issues_v2_last_updated', 'jira_issues_v2', ['last_updated'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_jira_issues_v2_last_updated', 'jira_issues_v2')
    op.drop_index('idx_jira_issues_v2_project_name', 'jira_issues_v2')
    op.drop_index('idx_jira_issues_v2_status', 'jira_issues_v2')
    op.drop_index('idx_jira_issues_v2_ndpu_listing_address', 'jira_issues_v2')
    op.drop_index('idx_jira_issues_v2_ndpu_order_number', 'jira_issues_v2')
    op.drop_index('idx_jira_issues_v2_summary', 'jira_issues_v2')