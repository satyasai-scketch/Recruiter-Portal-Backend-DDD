# app/domain/job_role/rules.py
from typing import List, Optional
from .entities import JobRole

class JobRoleBusinessRules:
    """Business rules for Job Role domain."""
    
    @staticmethod
    def validate_job_role_name_uniqueness(job_roles: List[JobRole], name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if job role name is unique within the system."""
        for job_role in job_roles:
            if job_role.id != exclude_id and job_role.name.lower().strip() == name.lower().strip():
                return False
        return True
    
    @staticmethod
    def is_valid_job_role_data(job_role: JobRole) -> List[str]:
        """Validate job role data and return list of validation errors."""
        errors = []
        
        # Name validation
        if not job_role.name or len(job_role.name.strip()) == 0:
            errors.append("Job role name is required")
        elif len(job_role.name.strip()) > 100:
            errors.append("Job role name cannot exceed 100 characters")
        
        # Description validation
        if job_role.description and len(job_role.description.strip()) > 1000:
            errors.append("Job role description cannot exceed 1000 characters")
        
        # Category validation
        if job_role.category and len(job_role.category.strip()) > 50:
            errors.append("Job role category cannot exceed 50 characters")
        
        return errors
    
    @staticmethod
    def can_delete_job_role(job_role: JobRole, has_job_descriptions: bool = False) -> bool:
        """Check if job role can be deleted."""
        # Job role cannot be deleted if it has associated job descriptions
        if has_job_descriptions:
            return False
        
        return True
    
    @staticmethod
    def get_job_role_search_criteria(name: Optional[str] = None, 
                                   category: Optional[str] = None,
                                   is_active: Optional[bool] = None) -> dict:
        """Get search criteria for job role filtering."""
        criteria = {}
        
        if name:
            criteria['name_contains'] = name.lower().strip()
        
        if category:
            criteria['category_contains'] = category.lower().strip()
        
        if is_active is not None:
            criteria['is_active'] = is_active
        
        return criteria
    
    @staticmethod
    def get_active_job_roles(job_roles: List[JobRole]) -> List[JobRole]:
        """Filter active job roles."""
        return [job_role for job_role in job_roles if job_role.is_active]
    
    @staticmethod
    def get_job_roles_by_category(job_roles: List[JobRole], category: str) -> List[JobRole]:
        """Filter job roles by category."""
        return [job_role for job_role in job_roles if job_role.category and job_role.category.lower() == category.lower()]
