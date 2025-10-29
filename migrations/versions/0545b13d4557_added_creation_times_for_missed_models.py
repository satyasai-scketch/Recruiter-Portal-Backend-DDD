# migrations/versions/0545b13d4557_added_creation_times_for_missed_models.py
"""added_creation times for missed models

Revision ID: 0545b13d4557
Revises: ee1b28c20928
Create Date: 2025-10-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "0545b13d4557"
down_revision: Union[str, None] = "ee1b28c20928"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) candidate_cvs.uploaded_at: fill NULLs, then enforce NOT NULL + default
    conn.execute(text("UPDATE candidate_cvs SET uploaded_at = CURRENT_TIMESTAMP WHERE uploaded_at IS NULL"))
    with op.batch_alter_table("candidate_cvs") as batch_op:
        batch_op.alter_column(
            "uploaded_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    # 2) candidates.created_at: fill NULLs, then enforce NOT NULL + default
    conn.execute(text("UPDATE candidates SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    # 3) candidates.updated_at: fill NULLs, then enforce NOT NULL + default
    conn.execute(text("UPDATE candidates SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade() -> None:
    # Best-effort revert: drop NOT NULL and defaults
    with op.batch_alter_table("candidate_cvs") as batch_op:
        batch_op.alter_column(
            "uploaded_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            server_default=None,
        )

    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            server_default=None,
        )

    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            server_default=None,
        )