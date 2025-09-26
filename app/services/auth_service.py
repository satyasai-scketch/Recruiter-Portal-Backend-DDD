from __future__ import annotations

from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.user import UserModel
from app.db.models.role import RoleModel
from app.repositories.user_repo import SQLAlchemyUserRepository
from app.core.security import get_password_hash, verify_password, create_access_token


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

	def signup(self, db: Session, email: str, password: str, role_name: Optional[str] = None) -> UserModel:
		existing = self.users.get_by_email(db, email)
		if existing:
			raise ValueError("Email already registered")
		role = self._get_or_create_default_role(db, role_name or "recruiter")
		user = UserModel(
			id=str(uuid4()),
			email=email,
			hashed_password=get_password_hash(password),
			is_active=True,
			role_id=role.id,
		)
		return self.users.create(db, user)

	def login(self, db: Session, email: str, password: str) -> str:
		user = self.users.get_by_email(db, email)
		if not user or not verify_password(password, user.hashed_password):
			raise ValueError("Invalid credentials")
		if not user.is_active:
			raise ValueError("Inactive user")
		return create_access_token(subject=user.id)
