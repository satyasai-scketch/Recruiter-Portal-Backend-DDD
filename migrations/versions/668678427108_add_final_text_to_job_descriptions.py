"""add final_text to job_descriptions

Revision ID: 668678427108
Revises: 3ef60fda6ce0
Create Date: 2025-09-24 17:24:11.395334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '668678427108'
down_revision: Union[str, None] = '3ef60fda6ce0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_descriptions', sa.Column('final_text', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_descriptions', 'final_text')
