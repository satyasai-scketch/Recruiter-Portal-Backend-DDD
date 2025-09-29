# app/api/v1/job_role.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.schemas.job_role import (
    JobRoleCreate,
    JobRoleUpdate,
    JobRoleRead,
    JobRoleSimple,
    JobRoleListResponse,
    JobRoleSearchRequest,
    JobRoleResponse
)
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.job_role_commands import CreateJobRole, UpdateJobRole, DeleteJobRole
from app.cqrs.queries.job_role_queries import (
    GetJobRole,
    GetJobRoleByName,
    ListJobRoles,
    ListActiveJobRoles,
    GetJobRolesByCategory,
    SearchJobRoles,
    CountJobRoles,
    CountActiveJobRoles,
    CountSearchJobRoles,
    GetJobRoleCategories
)
from app.domain.job_role.rules import JobRoleBusinessRules

router = APIRouter()

@router.post("/", response_model=JobRoleRead, summary="Create Job Role")
async def create_job_role(
    job_role_data: JobRoleCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Create a new job role.
    
    - **name**: Job role name (required)
    - **description**: Job role description (optional)
    - **category**: Job role category (optional)
    - **is_active**: Whether the job role is active (default: true)
    """
    try:
        # Convert Pydantic model to dict and add user info
        payload = job_role_data.model_dump()
        payload["created_by"] = user.id
        payload["updated_by"] = user.id
        
        # Create job role using CQRS
        created_job_role = handle_command(db, CreateJobRole(payload))
        
        return JobRoleRead.model_validate(created_job_role)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{job_role_id}", response_model=JobRoleRead, summary="Get Job Role by ID")
async def get_job_role(
    job_role_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get job role information by ID.
    """
    job_role = handle_query(db, GetJobRole(job_role_id))
    
    if not job_role:
        raise HTTPException(status_code=404, detail="Job role not found")
    
    return JobRoleRead.model_validate(job_role)

@router.get("/name/{job_role_name}", response_model=JobRoleRead, summary="Get Job Role by Name")
async def get_job_role_by_name(
    job_role_name: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get job role information by name.
    """
    job_role = handle_query(db, GetJobRoleByName(job_role_name))
    
    if not job_role:
        raise HTTPException(status_code=404, detail="Job role not found")
    
    return JobRoleRead.model_validate(job_role)

@router.get("/", response_model=JobRoleListResponse, summary="List Job Roles")
async def list_job_roles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    active_only: bool = Query(False, description="Show only active job roles"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    List all job roles with pagination.
    """
    skip = (page - 1) * size
    
    # Get job roles and total count
    if active_only:
        job_roles = handle_query(db, ListActiveJobRoles(skip, size))
        total = handle_query(db, CountActiveJobRoles())
    else:
        job_roles = handle_query(db, ListJobRoles(skip, size))
        total = handle_query(db, CountJobRoles())
    
    # Convert to response format
    job_role_reads = [JobRoleRead.model_validate(job_role) for job_role in job_roles]
    
    return JobRoleListResponse(
        job_roles=job_role_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )

@router.get("/category/{category}", response_model=JobRoleListResponse, summary="Get Job Roles by Category")
async def get_job_roles_by_category(
    category: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get job roles by category.
    """
    skip = (page - 1) * size
    
    # Get job roles by category
    job_roles = handle_query(db, GetJobRolesByCategory(category, skip, size))
    
    # For now, we'll use the same count as total (in a real app, you'd have a specific count method)
    total = len(job_roles)
    
    # Convert to response format
    job_role_reads = [JobRoleRead.model_validate(job_role) for job_role in job_roles]
    
    return JobRoleListResponse(
        job_roles=job_role_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )

@router.post("/search", response_model=JobRoleListResponse, summary="Search Job Roles")
async def search_job_roles(
    search_request: JobRoleSearchRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Search job roles based on criteria.
    
    - **name**: Search by job role name (optional)
    - **category**: Search by category (optional)
    - **is_active**: Filter by active status (optional)
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10)
    """
    skip = (search_request.page - 1) * search_request.size
    
    # Build search criteria
    search_criteria = JobRoleBusinessRules.get_job_role_search_criteria(
        name=search_request.name,
        category=search_request.category,
        is_active=search_request.is_active
    )
    
    # Get job roles and total count
    job_roles = handle_query(db, SearchJobRoles(search_criteria, skip, search_request.size))
    total = handle_query(db, CountSearchJobRoles(search_criteria))
    
    # Convert to response format
    job_role_reads = [JobRoleRead.model_validate(job_role) for job_role in job_roles]
    
    return JobRoleListResponse(
        job_roles=job_role_reads,
        total=total,
        page=search_request.page,
        size=search_request.size,
        has_next=(skip + search_request.size) < total,
        has_prev=search_request.page > 1
    )

@router.get("/simple/active", response_model=List[JobRoleSimple], summary="Get Active Job Roles (Simple)")
async def get_active_job_roles_simple(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get all active job roles in a simple format for dropdowns and selection.
    """
    job_roles = handle_query(db, ListActiveJobRoles(0, 1000))  # Get all active roles
    
    return [JobRoleSimple.model_validate(job_role) for job_role in job_roles]

@router.get("/categories", response_model=List[str], summary="Get Job Role Categories")
async def get_job_role_categories(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get all unique job role categories.
    """
    categories = handle_query(db, GetJobRoleCategories())
    return categories

@router.put("/{job_role_id}", response_model=JobRoleRead, summary="Update Job Role")
async def update_job_role(
    job_role_id: str,
    job_role_data: JobRoleUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Update job role information.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        # Convert Pydantic model to dict and add user info
        payload = job_role_data.model_dump(exclude_unset=True)
        payload["updated_by"] = user.id
        
        # Update job role using CQRS
        updated_job_role = handle_command(db, UpdateJobRole(job_role_id, payload))
        
        if not updated_job_role:
            raise HTTPException(status_code=404, detail="Job role not found")
        
        return JobRoleRead.model_validate(updated_job_role)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{job_role_id}", response_model=JobRoleResponse, summary="Delete Job Role")
async def delete_job_role(
    job_role_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Delete a job role.
    
    Job role cannot be deleted if it has associated job descriptions.
    """
    try:
        # Delete job role using CQRS
        success = handle_command(db, DeleteJobRole(job_role_id))
        
        if not success:
            raise HTTPException(status_code=404, detail="Job role not found")
        
        return JobRoleResponse(
            message="Job role deleted successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
