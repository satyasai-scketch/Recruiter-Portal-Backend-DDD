# app/db/models/company.py
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class CompanyModel(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    website_url = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    email_address = Column(String, nullable=True)
    
    # Address fields
    street = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    
    # Social media links
    twitter_link = Column(String, nullable=True)
    instagram_link = Column(String, nullable=True)
    facebook_link = Column(String, nullable=True)
    linkedin_link = Column(String, nullable=True)
    
    # Company description
    about_company = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("UserModel", foreign_keys=[created_by])
    updater = relationship("UserModel", foreign_keys=[updated_by])
    
    # Job descriptions associated with this company
    job_descriptions = relationship(
        "JobDescriptionModel",
        back_populates="company",
        cascade="all, delete-orphan"
    )
