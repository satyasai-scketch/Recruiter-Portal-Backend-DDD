# app/services/mfa_service.py
import secrets
import hashlib
import json
import time
import pyotp
import qrcode
from io import BytesIO
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.db.models.user import UserModel
from app.db.models.mfa import MFAModel, MFABackupCodeModel, MFALoginAttemptModel, MFAEmailOTPModel
from app.repositories.user_repo import SQLAlchemyUserRepository
from app.services.email.email_service import email_service


class MFAService:
    """Service for handling Multi-Factor Authentication operations."""

    def __init__(self, users: Optional[SQLAlchemyUserRepository] = None):
        self.users = users or SQLAlchemyUserRepository()

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def generate_totp_uri(self, secret: str, email: str) -> str:
        """Generate TOTP URI for QR code generation."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=settings.mfa_issuer_name
        )

    def generate_qr_code(self, uri: str) -> bytes:
        """Generate QR code image as bytes."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code against secret."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=settings.mfa_totp_window)

    def generate_backup_codes(self, count: int = None) -> List[str]:
        """Generate backup codes for MFA recovery."""
        if count is None:
            count = settings.mfa_backup_codes_count
        
        codes = []
        for _ in range(count):
            # Generate random code
            code = secrets.token_hex(settings.mfa_backup_code_length // 2)
            codes.append(code)
        
        return codes

    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """Hash backup codes for secure storage."""
        return [hashlib.sha256(code.encode()).hexdigest() for code in codes]

    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> bool:
        """Verify a backup code against hashed codes."""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        return code_hash in hashed_codes

    def setup_mfa(self, db: Session, user_id: str) -> Tuple[str, str, List[str]]:
        """Setup MFA for a user. Returns (secret, qr_code_uri, backup_codes)."""
        # Check if user already has MFA setup
        existing_mfa = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if existing_mfa and existing_mfa.totp_enabled:
            raise ValueError("MFA is already enabled for this user")

        # Generate TOTP secret
        secret = self.generate_totp_secret()
        
        # Get user email for QR code
        user = self.users.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        # Generate QR code URI
        qr_uri = self.generate_totp_uri(secret, user.email)
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes()
        hashed_codes = self.hash_backup_codes(backup_codes)

        # Create or update MFA record
        if existing_mfa:
            existing_mfa.totp_secret = secret
            existing_mfa.backup_codes = json.dumps(hashed_codes)
            existing_mfa.backup_codes_generated = True
            existing_mfa.updated_at = datetime.now(timezone.utc)
            db.commit()
            mfa_record = existing_mfa
        else:
            mfa_record = MFAModel(
                id=secrets.token_urlsafe(32),
                user_id=user_id,
                totp_secret=secret,
                backup_codes=json.dumps(hashed_codes),
                backup_codes_generated=True
            )
            db.add(mfa_record)
            db.commit()
            db.refresh(mfa_record)

        return secret, qr_uri, backup_codes

    def verify_mfa_setup(self, db: Session, user_id: str, totp_code: str) -> bool:
        """Verify MFA setup by checking TOTP code."""
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if not mfa_record or not mfa_record.totp_secret:
            raise ValueError("MFA not set up for this user")

        # Verify TOTP code
        if not self.verify_totp_code(mfa_record.totp_secret, totp_code):
            return False

        # Enable MFA
        mfa_record.totp_enabled = True
        mfa_record.totp_verified = True
        mfa_record.updated_at = datetime.now(timezone.utc)
        db.commit()

        return True

    def disable_mfa(self, db: Session, user_id: str, password: str) -> bool:
        """Disable MFA for a user (requires password verification)."""
        user = self.users.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid password")

        # Disable MFA
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if mfa_record:
            mfa_record.totp_enabled = False
            mfa_record.totp_verified = False
            mfa_record.totp_secret = None
            mfa_record.backup_codes = None
            mfa_record.backup_codes_generated = False
            mfa_record.updated_at = datetime.now(timezone.utc)
            db.commit()

        # Delete all backup code records
        db.query(MFABackupCodeModel).filter(MFABackupCodeModel.user_id == user_id).delete()
        db.commit()

        return True

    def verify_mfa_login(self, db: Session, user_id: str, mfa_code: str, 
                        ip_address: str = None, user_agent: str = None) -> bool:
        """Verify MFA code during login."""
        # System-level MFA check
        if not settings.mfa_enabled:
            raise ValueError("MFA is not enabled system-wide")
        
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if not mfa_record:
            raise ValueError("MFA setup required. Please enable Email OTP first.")
        
        if not mfa_record.email_otp_enabled:
            raise ValueError("Email OTP not enabled for this user. Please enable Email OTP first or contact support.")

        # Check for rate limiting
        if self._is_user_locked_out(db, user_id):
            raise ValueError("Account temporarily locked due to too many failed attempts")

        # Try Email OTP (only method available)
        if mfa_record.email_otp_enabled and self.verify_email_otp(db, user_id, mfa_code):
            self._record_login_attempt(db, user_id, "email_otp", True, ip_address, user_agent)
            return True

        # Try backup codes
        if mfa_record.backup_codes:
            hashed_codes = json.loads(mfa_record.backup_codes)
            if self.verify_backup_code(mfa_code, hashed_codes):
                # Mark backup code as used
                self._mark_backup_code_used(db, user_id, mfa_code)
                self._record_login_attempt(db, user_id, "backup_code", True, ip_address, user_agent)
                return True

        # Record failed attempt
        self._record_login_attempt(db, user_id, "email_otp", False, ip_address, user_agent)
        return False

    def regenerate_backup_codes(self, db: Session, user_id: str, password: str) -> List[str]:
        """Regenerate backup codes for a user."""
        user = self.users.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid password")

        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if not mfa_record or not mfa_record.totp_enabled:
            raise ValueError("MFA not enabled for this user")

        # Generate new backup codes
        backup_codes = self.generate_backup_codes()
        hashed_codes = self.hash_backup_codes(backup_codes)

        # Update MFA record
        mfa_record.backup_codes = json.dumps(hashed_codes)
        mfa_record.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Delete old backup code records
        db.query(MFABackupCodeModel).filter(MFABackupCodeModel.user_id == user_id).delete()
        db.commit()

        return backup_codes

    def generate_email_otp(self, length: int = None) -> str:
        """Generate a random OTP code for email."""
        if length is None:
            length = settings.mfa_email_otp_length
        
        # Generate numeric OTP
        import random
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
        
        # Check if user has Email OTP enabled
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
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

    def enable_email_otp(self, db: Session, user_id: str) -> bool:
        """Enable Email OTP for a user."""
        # System-level MFA check
        if not settings.mfa_enabled:
            raise ValueError("MFA is not enabled system-wide")
        
        if not settings.mfa_email_otp_enabled:
            raise ValueError("Email OTP is not enabled")
        
        # Get or create MFA record
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if not mfa_record:
            # Generate backup codes for new MFA setup
            backup_codes = self.generate_backup_codes()
            hashed_codes = self.hash_backup_codes(backup_codes)
            
            mfa_record = MFAModel(
                id=secrets.token_urlsafe(32),
                user_id=user_id,
                backup_codes=json.dumps(hashed_codes),
                backup_codes_generated=True
            )
            db.add(mfa_record)
        elif not mfa_record.backup_codes:
            # Generate backup codes if user doesn't have them
            backup_codes = self.generate_backup_codes()
            hashed_codes = self.hash_backup_codes(backup_codes)
            mfa_record.backup_codes = json.dumps(hashed_codes)
            mfa_record.backup_codes_generated = True
        
        mfa_record.email_otp_enabled = True
        mfa_record.email_otp_verified = True
        mfa_record.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return True

    def generate_backup_codes_for_user(self, db: Session, user_id: str) -> List[str]:
        """Generate new backup codes for a user and return them."""
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if not mfa_record:
            raise ValueError("MFA not set up for this user")
        
        # Get user information
        user = self.users.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Generate new backup codes
        backup_codes = self.generate_backup_codes()
        hashed_codes = self.hash_backup_codes(backup_codes)
        
        # Update MFA record with new backup codes
        mfa_record.backup_codes = json.dumps(hashed_codes)
        mfa_record.backup_codes_generated = True
        mfa_record.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Send backup codes via email
        try:
            from app.services.email.email_service import email_service
            email_service.send_backup_codes_email(
                to_email=user.email,
                backup_codes=backup_codes,
                user_name=f"{user.first_name} {user.last_name}"
            )
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Failed to send backup codes email: {e}")
        
        return backup_codes

    def auto_enable_mfa_for_user(self, db: Session, user_id: str) -> bool:
        """Automatically enable MFA for a user when system MFA is enabled."""
        if not settings.mfa_enabled:
            return False  # Don't auto-enable if system MFA is disabled
        
        if not settings.mfa_email_otp_enabled:
            return False  # Don't auto-enable if Email OTP is disabled
        
        # Check if user already has MFA record
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if mfa_record:
            return True  # Already has MFA record
        
        # Get user information for email
        user = self.users.get_by_id(db, user_id)
        if not user:
            return False  # User not found
        
        # Generate backup codes for new users
        backup_codes = self.generate_backup_codes()
        hashed_codes = self.hash_backup_codes(backup_codes)
        
        # Create MFA record and enable Email OTP with backup codes
        mfa_record = MFAModel(
            id=secrets.token_urlsafe(32),
            user_id=user_id,
            email_otp_enabled=True,
            email_otp_verified=True,
            backup_codes=json.dumps(hashed_codes),
            backup_codes_generated=True
        )
        db.add(mfa_record)
        db.commit()
        
        # Send backup codes via email to new user
        try:
            from app.services.email.email_service import email_service
            email_service.send_backup_codes_email(
                to_email=user.email,
                backup_codes=backup_codes,
                user_name=f"{user.first_name} {user.last_name}"
            )
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Failed to send backup codes email to new user: {e}")
        
        return True

    def disable_email_otp(self, db: Session, user_id: str) -> bool:
        """Disable Email OTP for a user."""
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        if mfa_record:
            mfa_record.email_otp_enabled = False
            mfa_record.email_otp_verified = False
            mfa_record.updated_at = datetime.now(timezone.utc)
            db.commit()
        
        # Clean up any pending OTP codes
        db.query(MFAEmailOTPModel).filter(
            MFAEmailOTPModel.user_id == user_id,
            MFAEmailOTPModel.used == False
        ).delete()
        db.commit()
        
        return True

    def get_mfa_status(self, db: Session, user_id: str) -> dict:
        """Get MFA status for a user."""
        # System-level MFA check - if disabled system-wide, return disabled
        if not settings.mfa_enabled:
            return {
                "enabled": False,
                "system_enabled": False,
                "email_otp_enabled": False,
                "email_otp_verified": False,
                "backup_codes_generated": False,
                "backup_codes_remaining": 0
            }
        
        # If system MFA is enabled, MFA is mandatory for all users
        # Check if user has MFA record, if not, they need to set it up
        mfa_record = db.query(MFAModel).filter(MFAModel.user_id == user_id).first()
        
        if not mfa_record:
            # User doesn't have MFA set up yet - they need to enable it
            return {
                "enabled": False,
                "system_enabled": True,
                "email_otp_enabled": False,
                "email_otp_verified": False,
                "backup_codes_generated": False,
                "backup_codes_remaining": 0,
                "setup_required": True
            }

        backup_codes_remaining = 0
        if mfa_record.backup_codes:
            hashed_codes = json.loads(mfa_record.backup_codes)
            used_codes = db.query(MFABackupCodeModel).filter(
                MFABackupCodeModel.user_id == user_id,
                MFABackupCodeModel.used_at.isnot(None)
            ).count()
            backup_codes_remaining = len(hashed_codes) - used_codes

        return {
            "enabled": mfa_record.email_otp_enabled,
            "system_enabled": True,
            "email_otp_enabled": mfa_record.email_otp_enabled,
            "email_otp_verified": mfa_record.email_otp_verified,
            "backup_codes_generated": mfa_record.backup_codes_generated,
            "backup_codes_remaining": backup_codes_remaining,
            "setup_required": False
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

    def _mark_backup_code_used(self, db: Session, user_id: str, code: str):
        """Mark a backup code as used."""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        used_code = MFABackupCodeModel(
            id=secrets.token_urlsafe(32),
            user_id=user_id,
            code_hash=code_hash,
            used_at=datetime.now(timezone.utc)
        )
        db.add(used_code)
        db.commit()
