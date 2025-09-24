from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.db.models.user import UserModel


class UserRepository:
	"""Repository interface for users."""

	def get_by_id(self, db: Session, user_id: str) -> Optional[UserModel]:
		raise NotImplementedError

	def get_by_email(self, db: Session, email: str) -> Optional[UserModel]:
		raise NotImplementedError

	def create(self, db: Session, user: UserModel) -> UserModel:
		raise NotImplementedError


class SQLAlchemyUserRepository(UserRepository):
	"""SQLAlchemy-backed user repository."""

	def get_by_id(self, db: Session, user_id: str) -> Optional[UserModel]:
		return db.get(UserModel, user_id)

	def get_by_email(self, db: Session, email: str) -> Optional[UserModel]:
		return db.query(UserModel).filter(UserModel.email == email).first()

	def create(self, db: Session, user: UserModel) -> UserModel:
		db.add(user)
		db.commit()
		db.refresh(user)
		return user
