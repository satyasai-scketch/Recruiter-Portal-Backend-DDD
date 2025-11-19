"""add_candidate_selections_table

Revision ID: e622012dc802
Revises: 8128f6a43853
Create Date: 2025-11-14 17:52:40.103052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e622012dc802'
down_revision: Union[str, None] = '8128f6a43853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists (in case migration partially ran before)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create candidate_selections table only if it doesn't exist
    if 'candidate_selections' not in existing_tables:
        op.create_table('candidate_selections',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('candidate_id', sa.String(), nullable=False, index=True),
            sa.Column('persona_id', sa.String(), nullable=False, index=True),
            sa.Column('job_description_id', sa.String(), nullable=False, index=True),
            sa.Column('selected_by', sa.String(), nullable=True, index=True),
            sa.Column('selection_notes', sa.Text(), nullable=True),
            sa.Column('priority', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='selected'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['selected_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('candidate_id', 'persona_id', name='uq_candidate_persona_selection')
        )
    
    # Get existing indexes to avoid duplicates
    existing_indexes = []
    if 'candidate_selections' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('candidate_selections')]
    
    # Create indexes for efficient querying (only if they don't exist)
    # Note: Column-level index=True in the model creates automatic indexes, but we also want named indexes
    index_definitions = [
        ('idx_candidate_selections_candidate', ['candidate_id']),
        ('idx_candidate_selections_persona', ['persona_id']),
        ('idx_candidate_selections_status', ['status']),
        ('idx_candidate_selections_jd', ['job_description_id']),
        ('ix_candidate_selections_selected_by', ['selected_by']),
    ]
    
    for index_name, columns in index_definitions:
        if index_name not in existing_indexes:
            try:
                op.create_index(index_name, 'candidate_selections', columns, unique=False)
            except Exception:
                # Index might already exist with different name, skip
                pass
    
    # Ensure personas.is_active is NOT NULL (use batch mode for SQLite)
    # Check if is_active column exists and is nullable
    personas_columns = {col['name']: col for col in inspector.get_columns('personas')}
    if 'is_active' in personas_columns:
        is_active_col = personas_columns['is_active']
        if is_active_col.get('nullable', True):
            # Use batch mode to alter column
            with op.batch_alter_table('personas', schema=None) as batch_op:
                batch_op.alter_column('is_active',
                    existing_type=sa.VARCHAR(),
                    nullable=False,
                    server_default='true')
    
    # Note: Foreign keys on existing tables (candidates.created_by, candidates.updated_by, 
    # candidate_cvs.uploaded_by, personas.updated_by) should already exist from previous migrations.
    # SQLite doesn't support adding foreign keys to existing tables without batch mode,
    # and these were likely added in earlier migrations, so we skip them here.


def downgrade() -> None:
    # Check if table exists before dropping
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'candidate_selections' in existing_tables:
        # Get existing indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('candidate_selections')]
        
        # Drop indexes for candidate_selections table (only if they exist)
        indexes_to_drop = [
            'ix_candidate_selections_selected_by',
            'idx_candidate_selections_jd',
            'idx_candidate_selections_status',
            'idx_candidate_selections_persona',
            'idx_candidate_selections_candidate',
        ]
        
        for index_name in indexes_to_drop:
            if index_name in existing_indexes:
                try:
                    op.drop_index(index_name, table_name='candidate_selections')
                except Exception:
                    # Index might not exist, skip
                    pass
        
        # Drop candidate_selections table
        op.drop_table('candidate_selections')
    
    # Revert personas.is_active to nullable (use batch mode for SQLite)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    personas_columns = {col['name']: col for col in inspector.get_columns('personas')}
    if 'is_active' in personas_columns:
        is_active_col = personas_columns['is_active']
        if not is_active_col.get('nullable', True):
            # Use batch mode to alter column
            with op.batch_alter_table('personas', schema=None) as batch_op:
                batch_op.alter_column('is_active',
                    existing_type=sa.VARCHAR(),
                    nullable=True,
                    server_default=None)
