"""add_candidate_selection_audit_logs_table

Revision ID: f8a9b2c3d4e5
Revises: e622012dc802
Create Date: 2025-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a9b2c3d4e5'
down_revision: Union[str, None] = 'e622012dc802'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists (in case migration partially ran before)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create candidate_selection_audit_logs table only if it doesn't exist
    if 'candidate_selection_audit_logs' not in existing_tables:
        op.create_table('candidate_selection_audit_logs',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('selection_id', sa.String(), nullable=False, index=True),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('changed_by', sa.String(), nullable=True, index=True),
            sa.Column('field_name', sa.String(), nullable=True),
            sa.Column('old_value', sa.Text(), nullable=True),
            sa.Column('new_value', sa.Text(), nullable=True),
            sa.Column('change_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['selection_id'], ['candidate_selections.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Get existing indexes to avoid duplicates
    existing_indexes = []
    if 'candidate_selection_audit_logs' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('candidate_selection_audit_logs')]
    
    # Create indexes for efficient querying (only if they don't exist)
    index_definitions = [
        ('idx_selection_audit_selection', ['selection_id']),
        ('idx_selection_audit_changed_by', ['changed_by']),
        ('idx_selection_audit_created_at', ['created_at']),
    ]
    
    for index_name, columns in index_definitions:
        if index_name not in existing_indexes:
            try:
                op.create_index(index_name, 'candidate_selection_audit_logs', columns, unique=False)
            except Exception:
                # Index might already exist with different name, skip
                pass


def downgrade() -> None:
    # Check if table exists before dropping
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'candidate_selection_audit_logs' in existing_tables:
        # Get existing indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('candidate_selection_audit_logs')]
        
        # Drop indexes for candidate_selection_audit_logs table (only if they exist)
        indexes_to_drop = [
            'idx_selection_audit_created_at',
            'idx_selection_audit_changed_by',
            'idx_selection_audit_selection',
        ]
        
        for index_name in indexes_to_drop:
            if index_name in existing_indexes:
                try:
                    op.drop_index(index_name, table_name='candidate_selection_audit_logs')
                except Exception:
                    # Index might not exist, skip
                    pass
        
        # Drop candidate_selection_audit_logs table
        op.drop_table('candidate_selection_audit_logs')

