# app/domain/job_role/entities.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class JobRole:
    """Job Role aggregate root."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    def __post_init__(self):
        """Validate job role data."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Job role name is required")
        
        if len(self.name.strip()) > 100:
            raise ValueError("Job role name cannot exceed 100 characters")
        
        if self.description and len(self.description.strip()) > 1000:
            raise ValueError("Job role description cannot exceed 1000 characters")
        
        if self.category and len(self.category.strip()) > 50:
            raise ValueError("Job role category cannot exceed 50 characters")
    
    def update_name(self, name: str) -> 'JobRole':
        """Update job role name."""
        return JobRole(
            id=self.id,
            name=name,
            description=self.description,
            category=self.category,
            is_active=self.is_active,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def update_description(self, description: str) -> 'JobRole':
        """Update job role description."""
        return JobRole(
            id=self.id,
            name=self.name,
            description=description,
            category=self.category,
            is_active=self.is_active,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def update_category(self, category: str) -> 'JobRole':
        """Update job role category."""
        return JobRole(
            id=self.id,
            name=self.name,
            description=self.description,
            category=category,
            is_active=self.is_active,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def activate(self) -> 'JobRole':
        """Activate the job role."""
        return JobRole(
            id=self.id,
            name=self.name,
            description=self.description,
            category=self.category,
            is_active=True,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def deactivate(self) -> 'JobRole':
        """Deactivate the job role."""
        return JobRole(
            id=self.id,
            name=self.name,
            description=self.description,
            category=self.category,
            is_active=False,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
