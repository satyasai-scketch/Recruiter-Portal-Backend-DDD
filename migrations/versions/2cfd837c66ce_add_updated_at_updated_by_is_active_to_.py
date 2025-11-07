"""add_updated_at_updated_by_is_active_to_personas

Revision ID: 2cfd837c66ce
Revises: fc7ca46d1ce0
Create Date: 2025-11-07 12:28:52.272686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cfd837c66ce'
down_revision: Union[str, None] = 'fc7ca46d1ce0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at, updated_by, and is_active columns to personas table
    # SQLite requires batch mode for all ALTER TABLE operations
    from sqlalchemy import text, inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('personas')]
    
    # Use batch_alter_table for all column additions and modifications
    with op.batch_alter_table('personas', schema=None) as batch_op:
        # Add updated_at column if it doesn't exist
        if 'updated_at' not in columns:
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
        # Add updated_by column if it doesn't exist
        if 'updated_by' not in columns:
            batch_op.add_column(sa.Column('updated_by', sa.String(), nullable=True))
        # Add is_active column if it doesn't exist
        if 'is_active' not in columns:
            batch_op.add_column(sa.Column('is_active', sa.String(), nullable=True))
    
    # Fill existing records with default values (safe to run even if columns already have values)
    conn.execute(text("UPDATE personas SET updated_at = created_at WHERE updated_at IS NULL"))
    conn.execute(text("UPDATE personas SET is_active = 'true' WHERE is_active IS NULL"))
    
    # Refresh column list after potential additions
    columns_after = [col['name'] for col in inspector.get_columns('personas')]
    
    # Now make columns NOT NULL with defaults if they exist and are currently nullable
    with op.batch_alter_table('personas', schema=None) as batch_op:
        if 'updated_at' in columns_after:
            updated_at_col = next((col for col in inspector.get_columns('personas') if col['name'] == 'updated_at'), None)
            if updated_at_col and updated_at_col.get('nullable', True):
                batch_op.alter_column('updated_at',
                                existing_type=sa.DateTime(timezone=True),
                                nullable=False,
                                server_default=sa.text('(CURRENT_TIMESTAMP)'))
        if 'is_active' in columns_after:
            is_active_col = next((col for col in inspector.get_columns('personas') if col['name'] == 'is_active'), None)
            if is_active_col and is_active_col.get('nullable', True):
                batch_op.alter_column('is_active',
                                existing_type=sa.String(),
                                nullable=False,
                                server_default='true')


def downgrade() -> None:
    # Remove the added columns using batch mode for SQLite
    with op.batch_alter_table('personas', schema=None) as batch_op:
        batch_op.drop_column('is_active')
        batch_op.drop_column('updated_by')
        batch_op.drop_column('updated_at')
