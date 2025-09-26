# app/db/models/role.py
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("UserModel", back_populates="role")