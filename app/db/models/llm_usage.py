"""
LLM Usage tracking model for storing AI usage metrics.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class LLMUsageModel(Base):
    """Model for tracking LLM API usage and costs"""
    __tablename__ = "llm_usage"
    
    id = Column(String, primary_key=True)
    
    # Hierarchy & Action Type
    action_type = Column(String, nullable=False, index=True)  # e.g., "JD_REFINE", "PERSONA_GEN"
    action_parent = Column(String, nullable=False, index=True)  # e.g., "JD", "PERSONA", "CV"
    action_name = Column(String, nullable=False)  # e.g., "jd_refinement", "persona_generation"
    
    # User Attribution
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Model Information
    provider = Column(String, nullable=False)  # "openai"
    model = Column(String, nullable=False, index=True)  # "gpt-4o", "gpt-4o-mini"
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    latency_ms = Column(Float, nullable=False)  # milliseconds
    
    # Token Usage & Costs
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    input_cost_usd = Column(Float, nullable=False, default=0.0)
    output_cost_usd = Column(Float, nullable=False, default=0.0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)
    
    # Context (optional metadata)
    context_data = Column(String, nullable=True)  # JSON string for additional context
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", backref="llm_usage_records")

