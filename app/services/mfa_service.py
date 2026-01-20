import secrets
import hashlib
import random
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.user import UserModel
from app.db.models.mfa import MFAModel, MFAEmailOTPModel, MFALoginAttemptModel
from app.repositories.user_repo import SQLAlchemyUserRepository
from app.services.email.email_service import email_service


class MFAService:
    """Service for handling Multi-Factor Authentication operations (Email OTP only)."""

    def __init__(self, users: Optional[SQLAlchemyUserRepository] = None):
        self.users = users or SQLAlchemyUserRepository()

    def _ensure_mfa_record_exists(self, db: Session, user_id: str) -> Optional[MFAModel]:
        """Ensure MFA record exists for user when system MFA is enabled."""
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        
        if not mfa_record and settings.mfa_enabled:
            # Auto-create MFA record with Email OTP enabled
            mfa_record = MFAModel(
                id=secrets.token_urlsafe(32),
                user_id=user_id,
                email_otp_enabled=True,
                email_otp_verified=True
            )
            db.add(mfa_record)
            db.commit()
            db.refresh(mfa_record)
        
        return mfa_record

    def generate_email_otp(self, length: int = None) -> str:
        """Generate a random OTP code for email."""
        if length is None:
            length = settings.mfa_email_otp_length
        
        # Generate numeric OTP
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    def send_email_otp(self, db: Session, user_id: str) -> bool:
        """Send Email OTP to user."""
        # System-level MFA check
        if not settings.mfa_enabled:
            raise ValueError("MFA is not enabled system-wide")
        
        if not settings.mfa_email_otp_enabled:
            raise ValueError("Email OTP is not enabled")
        
        user = self.users.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Ensure MFA record exists (auto-create if needed)
        mfa_record = self._ensure_mfa_record_exists(db, user_id)
        
        if not mfa_record or not mfa_record.email_otp_enabled:
            raise ValueError("Email OTP is not enabled for this user")
        
        # Generate OTP code
        otp_code = self.generate_email_otp()
        otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()
        
        # Set expiry time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.mfa_email_otp_expiry_minutes)
        
        # Create or update Email OTP record
        existing_otp = db.query(MFAEmailOTPModel).filter(
            MFAEmailOTPModel.user_id == user_id,
            MFAEmailOTPModel.used == False,
            MFAEmailOTPModel.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if existing_otp:
            # Update existing OTP
            existing_otp.otp_code = otp_hash
            existing_otp.expires_at = expires_at
            existing_otp.attempts = "0"
            existing_otp.created_at = datetime.now(timezone.utc)
        else:
            # Create new OTP record
            otp_record = MFAEmailOTPModel(
                id=secrets.token_urlsafe(32),
                user_id=user_id,
                otp_code=otp_hash,
                expires_at=expires_at
            )
            db.add(otp_record)
        
        db.commit()
        
        # Send email
        try:
            success = email_service.send_mfa_otp_email(
                to_email=user.email,
                otp_code=otp_code,
                user_name=f"{user.first_name} {user.last_name}",
                expiry_minutes=settings.mfa_email_otp_expiry_minutes
            )
            
            if not success:
                # If email fails, remove the OTP record
                db.query(MFAEmailOTPModel).filter(
                    MFAEmailOTPModel.user_id == user_id,
                    MFAEmailOTPModel.otp_code == otp_hash
                ).delete()
                db.commit()
                raise ValueError("Failed to send email OTP")
            
            return True
            
        except Exception as e:
            # Clean up OTP record on email failure
            db.query(MFAEmailOTPModel).filter(
                MFAEmailOTPModel.user_id == user_id,
                MFAEmailOTPModel.otp_code == otp_hash
            ).delete()
            db.commit()
            raise ValueError(f"Failed to send email OTP: {str(e)}")

    def verify_email_otp(self, db: Session, user_id: str, otp_code: str) -> bool:
        """Verify Email OTP code."""
        # System-level MFA check
        if not settings.mfa_enabled:
            raise ValueError("MFA is not enabled system-wide")
        
        if not settings.mfa_email_otp_enabled:
            raise ValueError("Email OTP is not enabled")
        
        # Find valid OTP record
        otp_record = db.query(MFAEmailOTPModel).filter(
            MFAEmailOTPModel.user_id == user_id,
            MFAEmailOTPModel.used == False,
            MFAEmailOTPModel.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not otp_record:
            raise ValueError("No valid OTP code found or code has expired")
        
        # Check attempt limit
        attempts = int(otp_record.attempts)
        if attempts >= settings.mfa_email_otp_max_attempts:
            # Mark as used to prevent further attempts
            otp_record.used = True
            db.commit()
            raise ValueError("Maximum verification attempts exceeded")
        
        # Verify OTP code
        otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()
        if otp_record.otp_code != otp_hash:
            # Increment attempt count
            otp_record.attempts = str(attempts + 1)
            db.commit()
            return False
        
        # Mark as used
        otp_record.used = True
        db.commit()
        
        return True

    def verify_mfa_login(self, db: Session, user_id: str, mfa_code: str, 
                        ip_address: str = None, user_agent: str = None) -> bool:
        """Verify MFA code during login (Email OTP only)."""
        # System-level MFA check
        if not settings.mfa_enabled:
            raise ValueError("MFA is not enabled system-wide")
        
        # Ensure MFA record exists (auto-create if needed)
        mfa_record = self._ensure_mfa_record_exists(db, user_id)
        
        if not mfa_record or not mfa_record.email_otp_enabled:
            raise ValueError("MFA not properly configured")

        # Check for rate limiting
        if self._is_user_locked_out(db, user_id):
            raise ValueError("Account temporarily locked due to too many failed attempts")

        # Verify Email OTP
        try:
            if self.verify_email_otp(db, user_id, mfa_code):
                self._record_login_attempt(db, user_id, "email_otp", True, ip_address, user_agent)
                return True
        except ValueError:
            # OTP verification failed (expired, invalid, etc.)
            pass

        # Record failed attempt
        self._record_login_attempt(db, user_id, "email_otp", False, ip_address, user_agent)
        return False

    def get_mfa_status(self, db: Session, user_id: str) -> dict:
        """Get MFA status for a user."""
        # System-level MFA check - if disabled, return disabled
        if not settings.mfa_enabled:
            return {
                "enabled": False,
                "system_enabled": False,
                "email_otp_enabled": False
            }
        
        # If system MFA is enabled, ensure record exists
        mfa_record = self._ensure_mfa_record_exists(db, user_id)
        
        return {
            "enabled": True,  # Always true when system MFA is on
            "system_enabled": True,
            "email_otp_enabled": True  # Always true when system MFA is on
        }

    def _is_user_locked_out(self, db: Session, user_id: str) -> bool:
        """Check if user is locked out due to too many failed attempts."""
        lockout_time = datetime.now(timezone.utc) - timedelta(minutes=settings.mfa_lockout_duration_minutes)
        
        failed_attempts = db.query(MFALoginAttemptModel).filter(
            MFALoginAttemptModel.user_id == user_id,
            MFALoginAttemptModel.success == False,
            MFALoginAttemptModel.created_at > lockout_time
        ).count()

        return failed_attempts >= settings.mfa_max_login_attempts

    def _record_login_attempt(self, db: Session, user_id: str, attempt_type: str, 
                            success: bool, ip_address: str = None, user_agent: str = None):
        """Record MFA login attempt."""
        attempt = MFALoginAttemptModel(
            id=secrets.token_urlsafe(32),
            user_id=user_id,
            attempt_type=attempt_type,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(attempt)
        db.commit()