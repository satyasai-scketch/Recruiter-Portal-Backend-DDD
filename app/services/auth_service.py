from __future__ import annotations

from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.user import UserModel
from app.repositories.user_repo import SQLAlchemyUserRepository
from app.core.security import get_password_hash, verify_password, create_access_token


class AuthService:
	"""Handles user signup and login flows."""

	def __init__(self, users: Optional[SQLAlchemyUserRepository] = None):
		self.users = users or SQLAlchemyUserRepository()

	def signup(self, db: Session, email: str, password: str) -> UserModel:
		existing = self.users.get_by_email(db, email)
		if existing:
			raise ValueError("Email already registered")
		user = UserModel(
			id=str(uuid4()),
			email=email,
			hashed_password=get_password_hash(password),
			is_active=True,
			roles=["recruiter"],
		)
		return self.users.create(db, user)

	def login(self, db: Session, email: str, password: str) -> str:
		user = self.users.get_by_email(db, email)
		if not user or not verify_password(password, user.hashed_password):
			raise ValueError("Invalid credentials")
		if not user.is_active:
			raise ValueError("Inactive user")
		return create_access_token(subject=user.id)
