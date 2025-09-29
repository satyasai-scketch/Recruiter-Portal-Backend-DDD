# app/db/models/job_role.py
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class JobRoleModel(Base):
    __tablename__ = "job_roles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # e.g., "Engineering", "Marketing", "Sales"
    is_active = Column(String, nullable=False, default="true")  # Store as string for SQLite compatibility
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("UserModel", foreign_keys=[created_by])
    updater = relationship("UserModel", foreign_keys=[updated_by])
    
    # Job descriptions that use this role
    job_descriptions = relationship(
        "JobDescriptionModel",
        back_populates="job_role",
        cascade="all, delete-orphan"
    )
