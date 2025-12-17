from __future__ import annotations

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models.user import UserModel
from app.repositories.user_repo import SQLAlchemyUserRepository


class UserService:
	"""Service for user operations."""

	def __init__(self, users: Optional[SQLAlchemyUserRepository] = None):
		self.users = users or SQLAlchemyUserRepository()

	def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[UserModel]:
		"""Get all users with pagination."""
		return self.users.get_all(db, skip, limit)

	def get_by_id(self, db: Session, user_id: str) -> Optional[UserModel]:
		"""Get a user by ID."""
		return self.users.get_by_id(db, user_id)

	def get_by_role_name(self, db: Session, role_name: str, skip: int = 0, limit: int = 100) -> List[UserModel]:
		"""Get users by role name."""
		return self.users.get_by_role_name(db, role_name, skip, limit)

	def update(self, db: Session, user_id: str, update_data: Dict[str, Any]) -> Optional[UserModel]:
		"""Update a user."""

		current_user = self.get_by_id(db,user_id)

		if not current_user:
			raise ValueError("User not found")
		

		# Validate role_id if provided
		if 'role_id' in update_data and update_data['role_id'] is not None:
			from app.repositories.role_repo import RoleRepository
			role_repo = RoleRepository()
			role = role_repo.get_by_id(db, update_data['role_id'])
			if not role:
				raise ValueError("Invalid role_id provided")
			
			current_role = current_user.role.name

			if current_role and current_role.lower().strip() == "admin":
				admin_users = self.get_by_role_name(db,current_role)

				if len(admin_users) == 1:
					raise ValueError("You are the only admin. Assign another admin before changing.")

		# Validate email uniqueness if email is being updated
		if 'email' in update_data and update_data['email'] is not None:
			existing_user = self.users.get_by_email(db, update_data['email'])
			if existing_user and existing_user.id != user_id:
				raise ValueError("Email already exists")

		return self.users.update(db, user_id, update_data)
