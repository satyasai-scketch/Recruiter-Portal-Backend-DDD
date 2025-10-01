# app/repositories/role_repo.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.role import RoleModel

class RoleRepository:
    """Repository for User Role data access operations."""
    
    def create(self, db: Session, role_data: dict) -> RoleModel:
        """Create a new role."""
        try:
            role = RoleModel(**role_data)
            db.add(role)
            db.commit()
            db.refresh(role)
            return role
        except Exception as e:
            db.rollback()
            raise e
    
    def get_by_id(self, db: Session, role_id: str) -> Optional[RoleModel]:
        """Get role by ID."""
        return db.query(RoleModel).filter(RoleModel.id == role_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[RoleModel]:
        """Get role by name (case-insensitive)."""
        return db.query(RoleModel).filter(
            func.lower(RoleModel.name) == name.lower().strip()
        ).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[RoleModel]:
        """Get all roles with pagination."""
        return db.query(RoleModel).offset(skip).limit(limit).all()
    
    def update(self, db: Session, role_id: str, role_data: dict) -> Optional[RoleModel]:
        """Update a role."""
        try:
            role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
            if not role:
                return None
            
            for key, value in role_data.items():
                if hasattr(role, key):
                    setattr(role, key, value)
            
            db.commit()
            db.refresh(role)
            return role
        except Exception as e:
            db.rollback()
            raise e
    
    def delete(self, db: Session, role_id: str) -> bool:
        """Delete a role."""
        try:
            role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
            if not role:
                return False
            
            db.delete(role)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
    
    def exists(self, db: Session, role_id: str) -> bool:
        """Check if role exists."""
        return db.query(RoleModel).filter(RoleModel.id == role_id).first() is not None
