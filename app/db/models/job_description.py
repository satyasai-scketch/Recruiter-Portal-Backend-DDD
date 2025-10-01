from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class JobDescriptionModel(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    role_id = Column(String, ForeignKey("job_roles.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    refined_text = Column(Text, nullable=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    
    # Document metadata fields
    original_document_filename = Column(String, nullable=True)
    original_document_size = Column(String, nullable=True)  # Store as string to avoid int overflow
    original_document_extension = Column(String, nullable=True)
    document_word_count = Column(String, nullable=True)
    document_character_count = Column(String, nullable=True)

    # New tracking fields
    selected_version = Column(String, nullable=True)  # 'original' or 'refined'
    selected_text = Column(Text, nullable=True)       # recruiter’s final text
    selected_edited = Column(Boolean, nullable=False, default=False)

    # Creator info
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Audit fields
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    personas = relationship(
        "PersonaModel",
        back_populates="job_description",
        cascade="all, delete-orphan",
    )

    creator = relationship("UserModel", foreign_keys=[created_by])  # specify which foreign key to use
    
    # Company relationship
    company = relationship("CompanyModel", back_populates="job_descriptions")
    
    # Job role relationship
    job_role = relationship("JobRoleModel", back_populates="job_descriptions")
