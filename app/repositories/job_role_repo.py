# app/repositories/job_role_repo.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.db.models.job_role import JobRoleModel

class JobRoleRepository:
    """Repository for Job Role data access operations."""
    
    def create(self, db: Session, job_role_data: dict) -> JobRoleModel:
        """Create a new job role."""
        try:
            job_role = JobRoleModel(**job_role_data)
            db.add(job_role)
            db.commit()
            db.refresh(job_role)
            return job_role
        except Exception as e:
            db.rollback()
            raise e
    
    def get_by_id(self, db: Session, job_role_id: str) -> Optional[JobRoleModel]:
        """Get job role by ID."""
        return db.query(JobRoleModel).filter(JobRoleModel.id == job_role_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[JobRoleModel]:
        """Get job role by name (case-insensitive)."""
        return db.query(JobRoleModel).filter(
            func.lower(JobRoleModel.name) == name.lower().strip()
        ).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Get all job roles with pagination."""
        return db.query(JobRoleModel).offset(skip).limit(limit).all()
    
    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Get all active job roles with pagination."""
        return db.query(JobRoleModel).filter(
            JobRoleModel.is_active == "true"
        ).offset(skip).limit(limit).all()
    
    def get_by_category(self, db: Session, category: str, skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Get job roles by category with pagination."""
        return db.query(JobRoleModel).filter(
            func.lower(JobRoleModel.category) == category.lower().strip()
        ).offset(skip).limit(limit).all()
    
    def search(self, db: Session, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Search job roles based on criteria."""
        query = db.query(JobRoleModel)
        
        # Apply search filters
        if 'name_contains' in search_criteria:
            query = query.filter(
                func.lower(JobRoleModel.name).contains(search_criteria['name_contains'])
            )
        
        if 'category_contains' in search_criteria:
            query = query.filter(
                func.lower(JobRoleModel.category).contains(search_criteria['category_contains'])
            )
        
        if 'is_active' in search_criteria:
            is_active_str = "true" if search_criteria['is_active'] else "false"
            query = query.filter(JobRoleModel.is_active == is_active_str)
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session) -> int:
        """Count total number of job roles."""
        return db.query(JobRoleModel).count()
    
    def count_active(self, db: Session) -> int:
        """Count active job roles."""
        return db.query(JobRoleModel).filter(JobRoleModel.is_active == "true").count()
    
    def count_search(self, db: Session, search_criteria: Dict[str, Any]) -> int:
        """Count job roles matching search criteria."""
        query = db.query(JobRoleModel)
        
        # Apply search filters
        if 'name_contains' in search_criteria:
            query = query.filter(
                func.lower(JobRoleModel.name).contains(search_criteria['name_contains'])
            )
        
        if 'category_contains' in search_criteria:
            query = query.filter(
                func.lower(JobRoleModel.category).contains(search_criteria['category_contains'])
            )
        
        if 'is_active' in search_criteria:
            is_active_str = "true" if search_criteria['is_active'] else "false"
            query = query.filter(JobRoleModel.is_active == is_active_str)
        
        return query.count()
    
    def update(self, db: Session, job_role: JobRoleModel) -> JobRoleModel:
        """Update an existing job role."""
        try:
            db.commit()
            db.refresh(job_role)
            return job_role
        except Exception as e:
            db.rollback()
            raise e
    
    def delete(self, db: Session, job_role_id: str) -> bool:
        """Delete a job role by ID."""
        try:
            job_role = self.get_by_id(db, job_role_id)
            if job_role:
                db.delete(job_role)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise e
    
    def check_name_exists(self, db: Session, name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if job role name exists (excluding specific ID)."""
        query = db.query(JobRoleModel).filter(
            func.lower(JobRoleModel.name) == name.lower().strip()
        )
        
        if exclude_id:
            query = query.filter(JobRoleModel.id != exclude_id)
        
        return query.first() is not None
    
    def get_job_roles_with_job_descriptions(self, db: Session) -> List[JobRoleModel]:
        """Get job roles that have associated job descriptions."""
        return db.query(JobRoleModel).join(
            JobRoleModel.job_descriptions
        ).distinct().all()
    
    def has_job_descriptions(self, db: Session, job_role_id: str) -> bool:
        """Check if job role has associated job descriptions."""
        job_role = self.get_by_id(db, job_role_id)
        if job_role:
            return len(job_role.job_descriptions) > 0
        return False
    
    def get_categories(self, db: Session) -> List[str]:
        """Get all unique categories."""
        categories = db.query(JobRoleModel.category).filter(
            JobRoleModel.category.isnot(None)
        ).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
