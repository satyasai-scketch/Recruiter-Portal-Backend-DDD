from __future__ import annotations

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from app.db.models.user import UserModel


class UserRepository:
	"""Repository interface for users."""

	def get_by_id(self, db: Session, user_id: str) -> Optional[UserModel]:
		raise NotImplementedError

	def get_by_email(self, db: Session, email: str) -> Optional[UserModel]:
		raise NotImplementedError

	def create(self, db: Session, user: UserModel) -> UserModel:
		raise NotImplementedError

	def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[UserModel]:
		raise NotImplementedError

	def update(self, db: Session, user_id: str, update_data: dict) -> Optional[UserModel]:
		raise NotImplementedError


class SQLAlchemyUserRepository(UserRepository):
	"""SQLAlchemy-backed user repository."""

	def get_by_id(self, db: Session, user_id: str) -> Optional[UserModel]:
		return (
			db.query(UserModel)
			.options(joinedload(UserModel.role))
			.filter(UserModel.id == user_id)
			.first()
		)

	def get_by_email(self, db: Session, email: str) -> Optional[UserModel]:
		return (
			db.query(UserModel)
			.options(joinedload(UserModel.role))
			.filter(UserModel.email == email)
			.first()
		)

	def create(self, db: Session, user: UserModel) -> UserModel:
		db.add(user)
		db.commit()
		db.refresh(user)
		return user

	def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[UserModel]:
		return (
			db.query(UserModel)
			.options(joinedload(UserModel.role))
			.offset(skip)
			.limit(limit)
			.all()
		)

	def update(self, db: Session, user_id: str, update_data: dict) -> Optional[UserModel]:
		user = self.get_by_id(db, user_id)
		if not user:
			return None
		
		for field, value in update_data.items():
			if hasattr(user, field) and value is not None:
				setattr(user, field, value)
		
		db.commit()
		db.refresh(user)
		return user
