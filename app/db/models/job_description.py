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
    role = Column(String, nullable=False)
    original_text = Column(Text, nullable=False)
    refined_text = Column(Text, nullable=True)
    company_id = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default=list)

    # New tracking fields
    selected_version = Column(String, nullable=True)  # 'original' or 'refined'
    selected_text = Column(Text, nullable=True)       # recruiter’s final text
    selected_edited = Column(Boolean, nullable=False, default=False)

    # Creator info
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    personas = relationship(
        "PersonaModel",
        back_populates="job_description",
        cascade="all, delete-orphan",
    )

    creator = relationship("UserModel")  # optional convenience relationship
