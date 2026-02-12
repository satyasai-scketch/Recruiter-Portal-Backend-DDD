from sqlalchemy import Column, String, Text, Integer, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class AIGeneratedPersonaModel(Base):
    """
    Pure AI-generated persona templates (full pipeline only).
    Completely separate from user personas.
    """
    __tablename__ = "ai_generated_personas"
    
    id = Column(String, primary_key=True)
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Complete AI output
    persona_json = Column(JSON, nullable=False)
    analysis_json = Column(JSON, nullable=False)
    weights_data_json = Column(JSON, nullable=False)
    
    # Metadata (extracted from analysis)
    job_title = Column(String, nullable=True)
    job_family = Column(String, nullable=True, index=True)
    seniority_level = Column(String, nullable=True, index=True)
    technical_intensity = Column(String, nullable=True)
    jd_text = Column(Text, nullable=False)
    
    # Generation tracking
    model_used = Column(String, nullable=True)
    generation_cost = Column(Numeric(10, 4), nullable=True)
    generation_time_seconds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to JD
    job_description = relationship("JobDescriptionModel", backref="ai_personas")
    
    __table_args__ = (
        UniqueConstraint("job_description_id", name="uq_ai_persona_jd"),
        Index("idx_ai_persona_family_seniority", "job_family", "seniority_level"),
    )


class PersonaAISourceMappingModel(Base):
    """
    Optional: Track which user personas were derived from which AI templates.
    Completely separate from both tables - just a mapping.
    """
    __tablename__ = "persona_ai_source_mappings"
    
    id = Column(String, primary_key=True)
    persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_persona_id = Column(String, ForeignKey("ai_generated_personas.id", ondelete="CASCADE"), nullable=False, index=True)
    generation_method = Column(String, nullable=False)  # "full_pipeline" | "adapted"
    similarity_score = Column(Numeric(5, 4), nullable=True)  # If adapted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("persona_id", name="uq_persona_ai_mapping"),
    )