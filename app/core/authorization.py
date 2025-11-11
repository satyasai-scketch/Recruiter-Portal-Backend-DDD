"""
Authorization utilities for role-based access control.

This module provides helpers to determine what resources a user can access
based on their role and relationships (e.g., JDs they created or are assigned to).
"""
from typing import List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.db.models.user import UserModel
from app.db.models.job_description import JobDescriptionModel
from app.db.models.jd_hiring_manager import JDHiringManagerMappingModel


def get_accessible_jd_ids(db: Session, user: UserModel) -> Optional[Set[str]]:
    """
    Get set of JD IDs that a user can access based on their role.
    
    Rules:
    - Admin/Recruiter: Can access all JDs (returns None, meaning no filter)
    - Hiring Manager: Can only access JDs they created OR are assigned to
    
    Returns:
        Set[str]: Set of accessible JD IDs, or None if user can access all JDs
    """
    role_name = user.role.name if user.role else None
    if role_name:
        role_name = role_name.lower().strip()
    
    # Admin and Recruiter can access all JDs (case-insensitive check)
    if role_name in ("admin", "recruiter"):
        return None
    
    # Hiring Manager can only access JDs they created or are assigned to
    if role_name in ("hiring manager", "hiring_manager"):
        # Get JDs created by this user
        created_jd_ids = (
            db.query(JobDescriptionModel.id)
            .filter(JobDescriptionModel.created_by == user.id)
            .all()
        )
        created_ids = {jd_id[0] for jd_id in created_jd_ids}
        
        # Get JDs assigned to this user
        assigned_jd_ids = (
            db.query(JDHiringManagerMappingModel.job_description_id)
            .filter(JDHiringManagerMappingModel.hiring_manager_id == user.id)
            .all()
        )
        assigned_ids = {jd_id[0] for jd_id in assigned_jd_ids}
        
        # Combine both sets
        return created_ids | assigned_ids
    
    # Unknown role - return empty set (no access)
    return set()


def can_access_jd(db: Session, user: UserModel, jd_id: str) -> bool:
    """
    Check if a user can access a specific JD.
    
    This is optimized to check only the specific JD rather than fetching all accessible JDs.
    
    Args:
        db: Database session
        user: User to check
        jd_id: JD ID to check access for
        
    Returns:
        bool: True if user can access the JD, False otherwise
    """
    role_name = user.role.name if user.role else None
    if role_name:
        role_name = role_name.lower().strip()
    
    # Admin and Recruiter can access all JDs (case-insensitive check)
    if role_name in ("admin", "recruiter"):
        return True
    
    # Hiring Manager: Check if this specific JD was created by them OR assigned to them
    if role_name in ("hiring manager", "hiring_manager"):
        # Optimized: Check only the specific JD instead of fetching all accessible JDs
        # This is O(1) instead of O(n) where n = number of accessible JDs
        
        # First check if JD was created by this user (fast, uses index on id and created_by)
        created_by_user = (
            db.query(JobDescriptionModel.id)
            .filter(
                JobDescriptionModel.id == jd_id,
                JobDescriptionModel.created_by == user.id
            )
            .first()
        )
        
        if created_by_user:
            return True
        
        # Then check if JD is assigned to this user (only if not created by them)
        # Uses index on job_description_id and hiring_manager_id
        assigned_to_user = (
            db.query(JDHiringManagerMappingModel.job_description_id)
            .filter(
                JDHiringManagerMappingModel.job_description_id == jd_id,
                JDHiringManagerMappingModel.hiring_manager_id == user.id
            )
            .first()
        )
        
        return assigned_to_user is not None
    
    # Unknown role - no access
    return False


def get_jd_access_filter(db: Session, user: UserModel):
    """
    Get SQLAlchemy filter condition for JDs based on user role.
    
    This can be used in repository queries to filter JDs automatically.
    Uses SQL JOIN/subquery for efficient filtering without fetching all IDs first.
    
    Returns:
        SQLAlchemy filter condition, or None if no filter needed
    """
    role_name = user.role.name if user.role else None
    if role_name:
        role_name = role_name.lower().strip()
    
    # Admin and Recruiter can access all JDs - no filter needed (case-insensitive check)
    if role_name in ("admin", "recruiter"):
        return None
    
    # Hiring Manager: Filter using SQL JOIN/subquery (more efficient than fetching all IDs)
    if role_name in ("hiring manager", "hiring_manager"):
        from sqlalchemy import exists
        
        # Return filter: JD created by user OR JD assigned to user
        # This is executed as a SQL subquery, no need to fetch all IDs into memory
        return or_(
            JobDescriptionModel.created_by == user.id,
            exists().where(
                and_(
                    JDHiringManagerMappingModel.job_description_id == JobDescriptionModel.id,
                    JDHiringManagerMappingModel.hiring_manager_id == user.id
                )
            )
        )
    
    # Unknown role - return condition that never matches (no access)
    return JobDescriptionModel.id == "NEVER_MATCH"

