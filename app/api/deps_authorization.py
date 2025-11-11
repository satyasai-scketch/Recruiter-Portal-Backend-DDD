"""
FastAPI dependencies for role-based authorization.

These dependencies can be used in API endpoints to automatically filter
queries based on user roles and access permissions.
"""
from typing import Optional, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.authorization import get_accessible_jd_ids, can_access_jd
from app.db.models.user import UserModel


def get_accessible_jd_ids_dependency(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[Set[str]]:
    """
    FastAPI dependency that returns accessible JD IDs for the current user.
    
    Returns:
        Set[str] of accessible JD IDs, or None if user can access all JDs
    """
    return get_accessible_jd_ids(db, user)


def require_jd_access(
    jd_id: str,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    FastAPI dependency that ensures user can access a specific JD.
    
    Distinguishes between:
    - 404 Not Found: JD doesn't exist
    - 403 Forbidden: JD exists but user doesn't have access
    
    Returns:
        The JD ID if access is granted
    """
    from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
    
    # First check if JD exists
    repo = SQLAlchemyJobDescriptionRepository()
    jd = repo.get(db, jd_id)
    
    if not jd:
        # JD doesn't exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    
    # JD exists, now check access
    if not can_access_jd(db, user, jd_id):
        # JD exists but user doesn't have access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not have permission to access this job description."
        )
    
    return jd_id

