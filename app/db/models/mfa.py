# app/db/models/mfa.py
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class MFAModel(Base):
    """Model for storing MFA configuration and secrets for users."""
    __tablename__ = "user_mfa"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    
    # Email OTP Configuration
    email_otp_enabled = Column(Boolean, nullable=False, default=False)
    email_otp_verified = Column(Boolean, nullable=False, default=False)
    
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    user = relationship("UserModel", back_populates="mfa")




class MFAEmailOTPModel(Base):
    """Model for storing Email OTP codes."""
    __tablename__ = "mfa_email_otp"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    otp_code = Column(String, nullable=False)  # Hashed OTP code
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    attempts = Column(String, nullable=False, default="0")  # Number of verification attempts
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    user = relationship("UserModel")


class MFALoginAttemptModel(Base):
    """Model for tracking MFA login attempts and rate limiting."""
    __tablename__ = "mfa_login_attempts"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    attempt_type = Column(String, nullable=False)  # 'totp', 'backup_code', 'email_otp', 'recovery'
    success = Column(Boolean, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    user = relationship("UserModel")
