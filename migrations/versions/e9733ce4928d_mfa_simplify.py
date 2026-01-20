"""mfa simplify

Revision ID: e9733ce4928d
Revises: b62a6078c98b
Create Date: 2026-01-16 13:37:35.632282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9733ce4928d'
down_revision: Union[str, None] = 'b62a6078c98b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Simplify MFA to Email OTP only - remove TOTP and backup codes."""
    
    # Drop backup codes table
    op.drop_table('mfa_backup_codes')
    
    # Create new simplified user_mfa table
    op.create_table(
        'user_mfa_new',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('email_otp_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('email_otp_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Copy existing data (only Email OTP fields)
    op.execute("""
        INSERT INTO user_mfa_new (id, user_id, email_otp_enabled, email_otp_verified, created_at, updated_at)
        SELECT id, user_id, 
               COALESCE(email_otp_enabled, 0), 
               COALESCE(email_otp_verified, 0), 
               created_at, 
               updated_at
        FROM user_mfa
    """)
    
    # Drop old table
    op.drop_table('user_mfa')
    
    # Rename new table
    op.execute('ALTER TABLE user_mfa_new RENAME TO user_mfa')


def downgrade() -> None:
    """Restore TOTP and backup codes (data will be lost)."""
    
    # Recreate backup codes table
    op.create_table(
        'mfa_backup_codes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create new user_mfa with all old fields
    op.create_table(
        'user_mfa_new',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('totp_secret', sa.String(), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('totp_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('email_otp_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('email_otp_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('backup_codes_generated', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('recovery_email', sa.String(), nullable=True),
        sa.Column('recovery_phone', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Copy data with defaults for removed fields
    op.execute("""
        INSERT INTO user_mfa_new (
            id, user_id, email_otp_enabled, email_otp_verified, created_at, updated_at,
            totp_secret, totp_enabled, totp_verified, backup_codes, backup_codes_generated,
            recovery_email, recovery_phone
        )
        SELECT 
            id, user_id, email_otp_enabled, email_otp_verified, created_at, updated_at,
            NULL, 0, 0, NULL, 0, NULL, NULL
        FROM user_mfa
    """)
    
    # Drop simplified table
    op.drop_table('user_mfa')
    
    # Rename
    op.execute('ALTER TABLE user_mfa_new RENAME TO user_mfa')