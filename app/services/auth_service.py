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
	            phone: Optional[str] = None, role_name: Optional[str] = None) -> UserModel:
		existing = self.users.get_by_email(db, email)
		if existing:
			raise ValueError("Email already registered")
		role = self._get_or_create_default_role(db, role_name or "recruiter")
		user = UserModel(
			id=str(uuid4()),
			email=email,
			hashed_password=get_password_hash(password),
			first_name=first_name,
			last_name=last_name,
			phone=phone,
			is_active=True,
			role_id=role.id,
		)
		created_user = self.users.create(db, user)
		
		# Send welcome email
		try:
			email_service.send_welcome_email(email, f"{first_name} {last_name}")
		except Exception as e:
			# Log error but don't fail signup
			print(f"Failed to send welcome email: {e}")
		
		return created_user

	def login(self, db: Session, email: str, password: str) -> str:
		user = self.users.get_by_email(db, email)
		if not user or not verify_password(password, user.hashed_password):
			raise ValueError("Invalid credentials")
		if not user.is_active:
			raise ValueError("Inactive user")
		return create_access_token(subject=user.id)
	
	def forgot_password(self, db: Session, email: str) -> bool:
		"""Initiate password reset process."""
		user = self.users.get_by_email(db, email)
		if not user:
			# Don't reveal if email exists or not for security
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
			email_service.send_password_reset_email(
				email, 
				reset_token, 
				f"{user.first_name} {user.last_name}"
			)
			return True
		except Exception as e:
			# Clear token if email fails
			user.reset_token = None
			user.reset_token_expires = None
			db.commit()
			raise ValueError(f"Failed to send reset email: {str(e)}")
	
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
