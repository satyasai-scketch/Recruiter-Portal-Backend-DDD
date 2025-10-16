"""candidate phase data modeling

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, create candidate_cvs table without foreign key constraint
    op.create_table('candidate_cvs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('candidate_id', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_hash', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('s3_url', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('skills', sqlite.JSON(), nullable=True),
        sa.Column('roles_detected', sqlite.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash')
    )
    
    # Create indexes for candidate_cvs
    op.create_index(op.f('ix_candidate_cvs_candidate_id'), 'candidate_cvs', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_candidate_cvs_file_hash'), 'candidate_cvs', ['file_hash'], unique=True)
    
    # Drop existing candidates table and recreate with new schema
    op.drop_table('candidates')
    
    # Create new candidates table with updated schema
    op.create_table('candidates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('latest_cv_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for candidates
    op.create_index(op.f('ix_candidates_email'), 'candidates', ['email'], unique=False)
    op.create_index(op.f('ix_candidates_phone'), 'candidates', ['phone'], unique=False)
    
    # Now add foreign key constraints
    op.create_foreign_key('fk_candidate_cvs_candidate_id', 'candidate_cvs', 'candidates', ['candidate_id'], ['id'])
    op.create_foreign_key('fk_candidates_latest_cv_id', 'candidates', 'candidate_cvs', ['latest_cv_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints first
    op.drop_constraint('fk_candidates_latest_cv_id', 'candidates', type_='foreignkey')
    op.drop_constraint('fk_candidate_cvs_candidate_id', 'candidate_cvs', type_='foreignkey')
    
    # Drop indexes
    op.drop_index(op.f('ix_candidates_phone'), table_name='candidates')
    op.drop_index(op.f('ix_candidates_email'), table_name='candidates')
    op.drop_index(op.f('ix_candidate_cvs_file_hash'), table_name='candidate_cvs')
    op.drop_index(op.f('ix_candidate_cvs_candidate_id'), table_name='candidate_cvs')
    
    # Drop tables
    op.drop_table('candidates')
    op.drop_table('candidate_cvs')
    
    # Recreate original candidates table
    op.create_table('candidates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('years_experience', sa.Float(), nullable=True),
        sa.Column('skills', sqlite.JSON(), nullable=False),
        sa.Column('education', sa.String(), nullable=True),
        sa.Column('cv_path', sa.String(), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('scores', sqlite.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
