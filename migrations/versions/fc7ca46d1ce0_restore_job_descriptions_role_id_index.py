"""restore_job_descriptions_role_id_index

Revision ID: fc7ca46d1ce0
Revises: 5cbac2151c28
Create Date: 2025-11-07 11:19:46.968320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc7ca46d1ce0'
down_revision: Union[str, None] = '5cbac2151c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Restore the role_id index that was accidentally dropped in migration b181357c3cf1
    # This index is critical for JOIN performance with job_roles table
    op.create_index(
        op.f('ix_job_descriptions_role_id'),
        'job_descriptions',
        ['role_id'],
        unique=False
    )


def downgrade() -> None:
    # Remove the index
    op.drop_index(op.f('ix_job_descriptions_role_id'), table_name='job_descriptions')
