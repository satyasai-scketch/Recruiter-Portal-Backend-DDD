"""add_audit_fields_to_candidates_and_cvs

Revision ID: a2af4fc90238
Revises: 2cfd837c66ce
Create Date: 2025-11-07 13:08:38.359579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2af4fc90238'
down_revision: Union[str, None] = '2cfd837c66ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add audit fields to candidates and candidate_cvs tables
    # SQLite requires batch mode for all ALTER TABLE operations
    from sqlalchemy import text, inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Add fields to candidates table
    candidates_columns = [col['name'] for col in inspector.get_columns('candidates')]
    
    with op.batch_alter_table('candidates', schema=None) as batch_op:
        if 'created_by' not in candidates_columns:
            batch_op.add_column(sa.Column('created_by', sa.String(), nullable=True))
        if 'updated_by' not in candidates_columns:
            batch_op.add_column(sa.Column('updated_by', sa.String(), nullable=True))
    
    # Add fields to candidate_cvs table
    cvs_columns = [col['name'] for col in inspector.get_columns('candidate_cvs')]
    
    with op.batch_alter_table('candidate_cvs', schema=None) as batch_op:
        if 'uploaded_by' not in cvs_columns:
            batch_op.add_column(sa.Column('uploaded_by', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the added columns using batch mode for SQLite
    from sqlalchemy import inspect
    
    inspector = inspect(op.get_bind())
    
    # Remove fields from candidates table
    candidates_columns = [col['name'] for col in inspector.get_columns('candidates')]
    with op.batch_alter_table('candidates', schema=None) as batch_op:
        if 'created_by' in candidates_columns:
            batch_op.drop_column('created_by')
        if 'updated_by' in candidates_columns:
            batch_op.drop_column('updated_by')
    
    # Remove fields from candidate_cvs table
    cvs_columns = [col['name'] for col in inspector.get_columns('candidate_cvs')]
    with op.batch_alter_table('candidate_cvs', schema=None) as batch_op:
        if 'uploaded_by' in cvs_columns:
            batch_op.drop_column('uploaded_by')
