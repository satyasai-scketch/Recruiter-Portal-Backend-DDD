"""add_jd_hiring_manager_mapping_table

Revision ID: 8128f6a43853
Revises: a2af4fc90238
Create Date: 2025-11-10 15:01:06.935256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8128f6a43853'
down_revision: Union[str, None] = 'a2af4fc90238'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check for existing tables from prototype/old structure and drop them if they exist
    # This handles both local dev (where prototype table exists) and server (where it doesn't)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Drop prototype/new table if it exists (from previous prototype attempt)
    # Note: In SQLite, dropping a table automatically drops its indexes
    if 'jd_hiring_manager_mappings' in existing_tables:
        op.drop_table('jd_hiring_manager_mappings')
    
    # Drop old jd_hiring_managers table if it exists (for migration from old structure)
    if 'jd_hiring_managers' in existing_tables:
        op.drop_table('jd_hiring_managers')
    
    # Now create the new jd_hiring_manager_mappings table with correct structure
    op.create_table('jd_hiring_manager_mappings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('job_description_id', sa.String(), nullable=False),
    sa.Column('hiring_manager_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['hiring_manager_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('job_description_id', 'hiring_manager_id', name='uq_jd_hiring_manager')
    )
    # Create indexes
    op.create_index(op.f('ix_jd_hiring_manager_mappings_hiring_manager_id'), 'jd_hiring_manager_mappings', ['hiring_manager_id'], unique=False)
    op.create_index(op.f('ix_jd_hiring_manager_mappings_job_description_id'), 'jd_hiring_manager_mappings', ['job_description_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_jd_hiring_manager_mappings_job_description_id'), table_name='jd_hiring_manager_mappings')
    op.drop_index(op.f('ix_jd_hiring_manager_mappings_hiring_manager_id'), table_name='jd_hiring_manager_mappings')
    # Drop table
    op.drop_table('jd_hiring_manager_mappings')
    
    # Recreate old jd_hiring_managers table if needed (for rollback purposes)
    # Note: This is optional - only if you need to restore the old structure
    # op.create_table('jd_hiring_managers',
    #     sa.Column('id', sa.VARCHAR(), nullable=False),
    #     sa.Column('job_description_id', sa.VARCHAR(), nullable=False),
    #     sa.Column('user_id', sa.VARCHAR(), nullable=False),
    #     sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    #     sa.Column('created_by', sa.VARCHAR(), nullable=True),
    #     sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    #     sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
    #     sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    #     sa.PrimaryKeyConstraint('id'),
    #     sa.UniqueConstraint('job_description_id', 'user_id', name='uq_jd_hiring_manager')
    # )
    # op.create_index('ix_jd_hiring_managers_user_id', 'jd_hiring_managers', ['user_id'], unique=False)
    # op.create_index('ix_jd_hiring_managers_job_description_id', 'jd_hiring_managers', ['job_description_id'], unique=False)
