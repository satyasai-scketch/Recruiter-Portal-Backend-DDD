from sqlalchemy import Column, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class JDHiringManagerMappingModel(Base):
    """Model for mapping Job Descriptions to Hiring Managers (many-to-many relationship)."""
    
    __tablename__ = "jd_hiring_manager_mappings"

    id = Column(String, primary_key=True)
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    hiring_manager_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Unique constraint to prevent duplicate mappings
    __table_args__ = (
        UniqueConstraint('job_description_id', 'hiring_manager_id', name='uq_jd_hiring_manager'),
    )
    
    # Relationships
    job_description = relationship("JobDescriptionModel", back_populates="hiring_manager_mappings")
    hiring_manager = relationship("UserModel", foreign_keys=[hiring_manager_id])
    creator = relationship("UserModel", foreign_keys=[created_by])

