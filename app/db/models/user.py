from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.sqlite import JSON

from app.db.base import Base


class UserModel(Base):
	__tablename__ = "users"

	id = Column(String, primary_key=True)
	email = Column(String, unique=True, index=True, nullable=False)
	hashed_password = Column(String, nullable=False)
	is_active = Column(Boolean, nullable=False, default=True)
	roles = Column(JSON, nullable=False, default=list)
