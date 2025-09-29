# app/domain/job_role/services.py
from typing import Optional
from datetime import datetime
from uuid import uuid4

from .entities import JobRole
from .rules import JobRoleBusinessRules

def create_job_role(
    name: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
    is_active: bool = True,
    created_by: Optional[str] = None
) -> JobRole:
    """Create a new job role with validation."""
    
    # Create job role entity
    job_role = JobRole(
        id=str(uuid4()),
        name=name,
        description=description,
        category=category,
        is_active=is_active,
        created_at=datetime.now(),
        created_by=created_by,
        updated_at=datetime.now(),
        updated_by=created_by
    )
    
    # Validate job role data
    validation_errors = JobRoleBusinessRules.is_valid_job_role_data(job_role)
    if validation_errors:
        raise ValueError(f"Job role validation failed: {', '.join(validation_errors)}")
    
    return job_role

def update_job_role(
    existing_job_role: JobRole,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    updated_by: Optional[str] = None
) -> JobRole:
    """Update an existing job role with validation."""
    
    # Update job role entity
    updated_job_role = JobRole(
        id=existing_job_role.id,
        name=name if name is not None else existing_job_role.name,
        description=description if description is not None else existing_job_role.description,
        category=category if category is not None else existing_job_role.category,
        is_active=is_active if is_active is not None else existing_job_role.is_active,
        created_at=existing_job_role.created_at,
        created_by=existing_job_role.created_by,
        updated_at=datetime.now(),
        updated_by=updated_by
    )
    
    # Validate updated job role data
    validation_errors = JobRoleBusinessRules.is_valid_job_role_data(updated_job_role)
    if validation_errors:
        raise ValueError(f"Job role validation failed: {', '.join(validation_errors)}")
    
    return updated_job_role

def validate_job_role_uniqueness(
    job_roles: list,
    name: str,
    exclude_id: Optional[str] = None
) -> None:
    """Validate that job role name is unique within the system."""
    
    # Check name uniqueness
    if not JobRoleBusinessRules.validate_job_role_name_uniqueness(job_roles, name, exclude_id):
        raise ValueError("Job role name must be unique")
