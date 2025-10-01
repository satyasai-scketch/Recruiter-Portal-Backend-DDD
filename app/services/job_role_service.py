# app/services/job_role_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.job_role_repo import JobRoleRepository
from app.domain.job_role.entities import JobRole
from app.domain.job_role.services import (
    create_job_role as create_job_role_domain,
    update_job_role as update_job_role_domain,
    validate_job_role_uniqueness
)
from app.domain.job_role.rules import JobRoleBusinessRules
from app.db.models.job_role import JobRoleModel
from app.events.job_role_events import JobRoleCreatedEvent, JobRoleUpdatedEvent, JobRoleDeletedEvent
from app.events.event_bus import event_bus

class JobRoleService:
    """Application service for Job Role operations."""
    
    def __init__(self):
        self.repo = JobRoleRepository()
    
    def create(self, db: Session, data: dict) -> JobRoleModel:
        """Create a new job role."""
        try:
            # Extract data for domain service
            name = data.get("name")
            description = data.get("description")
            category = data.get("category")
            is_active = data.get("is_active", True)
            created_by = data.get("created_by")
            
            # Get all existing job roles for uniqueness validation
            existing_job_roles = self.repo.get_all(db)
            existing_job_roles_domain = [self._model_to_domain(job_role) for job_role in existing_job_roles]
            
            # Validate uniqueness
            validate_job_role_uniqueness(existing_job_roles_domain, name)
            
            # Create domain entity
            job_role_domain = create_job_role_domain(
                name=name,
                description=description,
                category=category,
                is_active=is_active,
                created_by=created_by
            )
            
            # Convert to model data
            model_data = self._domain_to_model_data(job_role_domain)
            
            # Create in database
            created_job_role = self.repo.create(db, model_data)
            
            # Publish event (with error handling)
            try:
                event_bus.publish_event(JobRoleCreatedEvent(
                    job_role_id=created_job_role.id,
                    job_role_name=created_job_role.name,
                    created_by=created_by
                ))
            except Exception as e:
                print(f"Failed to publish JobRoleCreatedEvent: {e}")
            
            return created_job_role
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_by_id(self, db: Session, job_role_id: str) -> Optional[JobRoleModel]:
        """Get job role by ID."""
        return self.repo.get_by_id(db, job_role_id)
    
    def get_by_name(self, db: Session, name: str) -> Optional[JobRoleModel]:
        """Get job role by name."""
        return self.repo.get_by_name(db, name)
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Get all job roles with pagination."""
        return self.repo.get_all(db, skip, limit)
    
    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Get all active job roles with pagination."""
        return self.repo.get_active(db, skip, limit)
    
    def get_by_category(self, db: Session, category: str, skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Get job roles by category with pagination."""
        return self.repo.get_by_category(db, category, skip, limit)
    
    def search(self, db: Session, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[JobRoleModel]:
        """Search job roles based on criteria."""
        return self.repo.search(db, search_criteria, skip, limit)
    
    def count(self, db: Session) -> int:
        """Count total number of job roles."""
        return self.repo.count(db)
    
    def count_active(self, db: Session) -> int:
        """Count active job roles."""
        return self.repo.count_active(db)
    
    def count_search(self, db: Session, search_criteria: Dict[str, Any]) -> int:
        """Count job roles matching search criteria."""
        return self.repo.count_search(db, search_criteria)
    
    def update(self, db: Session, job_role_id: str, data: dict) -> Optional[JobRoleModel]:
        """Update an existing job role."""
        try:
            existing_job_role = self.repo.get_by_id(db, job_role_id)
            if not existing_job_role:
                return None
            
            # Get all existing job roles for uniqueness validation
            existing_job_roles = self.repo.get_all(db)
            existing_job_roles_domain = [self._model_to_domain(job_role) for job_role in existing_job_roles]
            
            # Extract updated data
            name = data.get("name", existing_job_role.name)
            
            # Validate uniqueness
            validate_job_role_uniqueness(existing_job_roles_domain, name, exclude_id=job_role_id)
            
            # Convert existing model to domain entity
            existing_job_role_domain = self._model_to_domain(existing_job_role)
            
            # Update domain entity
            updated_job_role_domain = update_job_role_domain(
                existing_job_role_domain,
                name=data.get("name"),
                description=data.get("description"),
                category=data.get("category"),
                is_active=data.get("is_active"),
                updated_by=data.get("updated_by")
            )
            
            # Update model with new data
            self._update_model_from_domain(existing_job_role, updated_job_role_domain)
            
            # Save to database
            updated_job_role = self.repo.update(db, existing_job_role)
            
            # Publish event (with error handling)
            try:
                event_bus.publish_event(JobRoleUpdatedEvent(
                    job_role_id=updated_job_role.id,
                    job_role_name=updated_job_role.name,
                    updated_by=data.get("updated_by")
                ))
            except Exception as e:
                print(f"Failed to publish JobRoleUpdatedEvent: {e}")
            
            return updated_job_role
            
        except Exception as e:
            db.rollback()
            raise e
    
    def delete(self, db: Session, job_role_id: str) -> bool:
        """Delete a job role."""
        try:
            job_role = self.repo.get_by_id(db, job_role_id)
            if not job_role:
                return False
            
            # Check if job role can be deleted
            has_job_descriptions = self.repo.has_job_descriptions(db, job_role_id)
            job_role_domain = self._model_to_domain(job_role)
            
            if not JobRoleBusinessRules.can_delete_job_role(job_role_domain, has_job_descriptions):
                raise ValueError("Cannot delete job role with associated job descriptions")
            
            # Delete job role
            success = self.repo.delete(db, job_role_id)
            
            if success:
                # Publish event (with error handling)
                try:
                    event_bus.publish_event(JobRoleDeletedEvent(
                        job_role_id=job_role_id,
                        job_role_name=job_role.name
                    ))
                except Exception as e:
                    print(f"Failed to publish JobRoleDeletedEvent: {e}")
            
            return success
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_categories(self, db: Session) -> List[str]:
        """Get all unique categories."""
        return self.repo.get_categories(db)
    
    def _model_to_domain(self, model: JobRoleModel) -> JobRole:
        """Convert JobRoleModel to JobRole domain entity."""
        return JobRole(
            id=model.id,
            name=model.name,
            description=model.description,
            category=model.category,
            is_active=model.is_active == "true",
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by
        )
    
    def _domain_to_model_data(self, domain: JobRole) -> dict:
        """Convert JobRole domain entity to model data dictionary."""
        return {
            "id": domain.id,
            "name": domain.name,
            "description": domain.description,
            "category": domain.category,
            "is_active": "true" if domain.is_active else "false",
            "created_at": domain.created_at,
            "created_by": domain.created_by,
            "updated_at": domain.updated_at,
            "updated_by": domain.updated_by
        }
    
    def _update_model_from_domain(self, model: JobRoleModel, domain: JobRole) -> None:
        """Update JobRoleModel from JobRole domain entity."""
        model.name = domain.name
        model.description = domain.description
        model.category = domain.category
        model.is_active = "true" if domain.is_active else "false"
        model.updated_at = domain.updated_at
        model.updated_by = domain.updated_by
