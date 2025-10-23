from __future__ import annotations

from typing import Optional
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import secrets

from app.db.models.user import UserModel
from app.db.models.role import RoleModel
from app.repositories.user_repo import SQLAlchemyUserRepository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.services.email.email_service import email_service
from app.services.mfa_service import MFAService
from app.core.config import settings


class AuthService:
	"""Handles user signup and login flows."""

	def __init__(self, users: Optional[SQLAlchemyUserRepository] = None):
		self.users = users or SQLAlchemyUserRepository()

	def _get_or_create_default_role(self, db: Session, name: str = "recruiter") -> RoleModel:
		role = db.query(RoleModel).filter(RoleModel.name == name).first()
		if role:
			return role
		role = RoleModel(id=str(uuid4()), name=name)
		db.add(role)
		db.commit()
		db.refresh(role)
		return role

	def signup(self, db: Session, email: str, password: str, first_name: str, last_name: str, 
	            phone: Optional[str] = None, role_id: Optional[str] = None) -> UserModel:
		existing = self.users.get_by_email(db, email)
		if existing:
			raise ValueError("Email already registered")
		
		# Validate role_id if provided
		if role_id:
			from app.repositories.role_repo import RoleRepository
			role_repo = RoleRepository()
			role = role_repo.get_by_id(db, role_id)
			if not role:
				raise ValueError("Invalid role_id provided")
		else:
			# Use default role if no role_id provided
			role = self._get_or_create_default_role(db, "recruiter")
			role_id = role.id
		
		user = UserModel(
			id=str(uuid4()),
			email=email,
			hashed_password=get_password_hash(password),
			first_name=first_name,
			last_name=last_name,
			phone=phone,
			is_active=True,
			role_id=role_id,
		)
		created_user = self.users.create(db, user)
		
		# Auto-enable MFA for new users if system MFA is enabled
		if settings.mfa_enabled:
			try:
				mfa_service = MFAService()
				mfa_service.auto_enable_mfa_for_user(db, created_user.id)
			except Exception as e:
				# Log error but don't fail signup
				print(f"Failed to auto-enable MFA for new user: {e}")
		
		# Send welcome email
		try:
			email_service.send_welcome_email(email, f"{first_name} {last_name}")
		except Exception as e:
			# Log error but don't fail signup
			print(f"Failed to send welcome email: {e}")
		
		return created_user

	def login(self, db: Session, email: str, password: str) -> dict:
		user = self.users.get_by_email(db, email)
		if not user or not verify_password(password, user.hashed_password):
			raise ValueError("Invalid credentials")
		if not user.is_active:
			raise ValueError("Inactive user")
		
		# Check if MFA is enabled and required (system-level check)
		mfa_required = False
		mfa_token = None
		
		if settings.mfa_enabled:
			mfa_service = MFAService()
			mfa_status = mfa_service.get_mfa_status(db, user.id)
			# MFA is required if system MFA is enabled AND user has MFA enabled
			if mfa_status["system_enabled"] and mfa_status["enabled"]:
				mfa_required = True
				# Create temporary MFA token (short-lived)
				mfa_token = create_access_token(subject=user.id, expires_minutes=5)
		
		if mfa_required:
			return {
				"access_token": None,
				"token_type": "bearer",
				"user": user,
				"mfa_required": True,
				"mfa_token": mfa_token
			}
		else:
			return {
				"access_token": create_access_token(subject=user.id),
				"token_type": "bearer",
				"user": user,
				"mfa_required": False,
				"mfa_token": None
			}
	
	def verify_mfa_login(self, db: Session, mfa_token: str, mfa_code: str) -> str:
		"""Verify MFA code and return final access token."""
		from app.core.security import decode_token
		
		# Decode MFA token to get user ID
		token_data = decode_token(mfa_token)
		if not token_data:
			raise ValueError("Invalid or expired MFA token")
		
		user_id = token_data.get("sub")
		if not user_id:
			raise ValueError("Invalid MFA token")
		
		# Verify MFA code
		mfa_service = MFAService()
		success = mfa_service.verify_mfa_login(db, user_id, mfa_code)
		
		if not success:
			raise ValueError("Invalid MFA code")
		
		# Return final access token
		return create_access_token(subject=user_id)
	
	def forgot_password(self, db: Session, email: str) -> bool:
		"""Initiate password reset process."""
		user = self.users.get_by_email(db, email)
		if not user:
			# Don't reveal if email exists or not for security
			# Always return True to prevent email enumeration
			return True
		
		# Generate secure reset token
		reset_token = secrets.token_urlsafe(32)
		reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
		
		# Update user with reset token
		user.reset_token = reset_token
		user.reset_token_expires = reset_token_expires
		db.commit()
		
		# Send reset email
		try:
			email_sent = email_service.send_password_reset_email(
				email, 
				reset_token, 
				f"{user.first_name} {user.last_name}"
			)
			
			if not email_sent:
				# Clear token if email sending failed
				user.reset_token = None
				user.reset_token_expires = None
				db.commit()
				# Log the error but don't reveal it to the user for security
				print(f"Failed to send password reset email to {email}")
				# Still return True to prevent email enumeration
				return True
			
			return True
		except Exception as e:
			# Clear token if email fails
			user.reset_token = None
			user.reset_token_expires = None
			db.commit()
			# Log the error but don't reveal it to the user for security
			print(f"Failed to send password reset email to {email}: {str(e)}")
			# Still return True to prevent email enumeration
			return True
	
	def reset_password(self, db: Session, token: str, new_password: str) -> bool:
		"""Reset password using token."""
		user = db.query(UserModel).filter(
			UserModel.reset_token == token,
			UserModel.reset_token_expires > datetime.now(timezone.utc)
		).first()
		
		if not user:
			raise ValueError("Invalid or expired reset token")
		
		# Update password and clear reset token
		user.hashed_password = get_password_hash(new_password)
		user.reset_token = None
		user.reset_token_expires = None
		db.commit()
		
		return True
