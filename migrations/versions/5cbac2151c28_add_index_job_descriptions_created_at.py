"""add_index_job_descriptions_created_at

Revision ID: 5cbac2151c28
Revises: ca8f499269db
Create Date: 2025-11-06 16:00:06.042532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cbac2151c28'
down_revision: Union[str, None] = 'ca8f499269db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on job_descriptions.created_at for efficient ORDER BY queries
    # This is critical for the "List All JDs" API which orders by created_at DESC
    # with pagination (OFFSET/LIMIT)
    # Note: SQLite doesn't support DESC indexes, but the index still helps with sorting
    op.create_index(
        op.f('ix_job_descriptions_created_at'),
        'job_descriptions',
        ['created_at'],
        unique=False
    )


def downgrade() -> None:
    # Remove the index
    op.drop_index(op.f('ix_job_descriptions_created_at'), table_name='job_descriptions')
