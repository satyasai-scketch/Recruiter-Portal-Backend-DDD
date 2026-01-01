"""add jd_text column to ai_generated_personas

Revision ID: 01c54b333beb
Revises: 6e277fc74821
Create Date: 2025-11-20 14:28:47.514084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01c54b333beb'
down_revision: Union[str, None] = '6e277fc74821'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ai_generated_personas',
        sa.Column('jd_text', sa.Text(), nullable=True)
    )



def downgrade() -> None:
    op.drop_column('ai_generated_personas', 'jd_text')
