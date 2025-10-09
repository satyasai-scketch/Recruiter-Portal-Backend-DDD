"""add index job_descriptions role_id

Revision ID: a1b2c3d4e5f6
Revises: df1a9faecb7e
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'df1a9faecb7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on job_descriptions.role_id for better JOIN performance
    op.create_index(op.f('ix_job_descriptions_role_id'), 'job_descriptions', ['role_id'], unique=False)


def downgrade() -> None:
    # Remove the index
    op.drop_index(op.f('ix_job_descriptions_role_id'), table_name='job_descriptions')
