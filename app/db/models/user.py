# app/db/models/user.py
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Personal information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    
    # Password reset fields
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    role = relationship("RoleModel", back_populates="users")
    
    # MFA relationship
    mfa = relationship("MFAModel", back_populates="user", uselist=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
