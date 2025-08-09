"""Add performance metrics table

Revision ID: 002
Revises: 001
Create Date: 2025-08-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sync_performance_metrics table
    op.create_table('sync_performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_id', sa.String(255), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(50)),
        sa.Column('recorded_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['sync_id'], ['sync_history.sync_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_sync_performance_metrics_sync_id', 'sync_performance_metrics', ['sync_id'])
    op.create_index('idx_sync_performance_metrics_name', 'sync_performance_metrics', ['metric_name'])
    op.create_index('idx_sync_performance_metrics_recorded', 'sync_performance_metrics', ['recorded_at'])


def downgrade() -> None:
    # Drop the table
    op.drop_table('sync_performance_metrics')