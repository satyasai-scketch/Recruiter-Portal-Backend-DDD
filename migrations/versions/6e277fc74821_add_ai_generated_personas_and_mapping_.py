"""add_ai_generated_personas_and_mapping_tables

Revision ID: 6e277fc74821
Revises: 8128f6a43853
Create Date: 2025-11-18 12:44:50.745688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

# revision identifiers, used by Alembic.
revision: str = '6e277fc74821'
down_revision: Union[str, None] = '8128f6a43853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== CREATE ai_generated_personas TABLE ==========
    op.create_table(
        'ai_generated_personas',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_description_id', sa.String(), nullable=False),
        sa.Column('persona_json', JSON(), nullable=False),
        sa.Column('analysis_json', JSON(), nullable=False),
        sa.Column('weights_data_json', JSON(), nullable=False),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('job_family', sa.String(), nullable=True),
        sa.Column('seniority_level', sa.String(), nullable=True),
        sa.Column('technical_intensity', sa.String(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('generation_cost', sa.Numeric(10, 4), nullable=True),
        sa.Column('generation_time_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['job_description_id'], ['job_descriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_description_id', name='uq_ai_persona_jd')
    )
    
    # Create indexes for ai_generated_personas
    op.create_index(
        'idx_ai_persona_jd',
        'ai_generated_personas',
        ['job_description_id'],
        unique=False
    )
    op.create_index(
        'idx_ai_persona_family_seniority',
        'ai_generated_personas',
        ['job_family', 'seniority_level'],
        unique=False
    )
    
    # ========== CREATE persona_ai_source_mappings TABLE ==========
    op.create_table(
        'persona_ai_source_mappings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('ai_persona_id', sa.String(), nullable=False),
        sa.Column('generation_method', sa.String(), nullable=False),
        sa.Column('similarity_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_persona_id'], ['ai_generated_personas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('persona_id', name='uq_persona_ai_mapping')
    )
    
    # Create indexes for persona_ai_source_mappings
    op.create_index(
        'idx_mapping_persona',
        'persona_ai_source_mappings',
        ['persona_id'],
        unique=False
    )
    op.create_index(
        'idx_mapping_ai_persona',
        'persona_ai_source_mappings',
        ['ai_persona_id'],
        unique=False
    )


def downgrade() -> None:
    # Drop tables in reverse order (mappings first due to foreign keys)
    op.drop_index('idx_mapping_ai_persona', table_name='persona_ai_source_mappings')
    op.drop_index('idx_mapping_persona', table_name='persona_ai_source_mappings')
    op.drop_table('persona_ai_source_mappings')
    
    op.drop_index('idx_ai_persona_family_seniority', table_name='ai_generated_personas')
    op.drop_index('idx_ai_persona_jd', table_name='ai_generated_personas')
    op.drop_table('ai_generated_personas')