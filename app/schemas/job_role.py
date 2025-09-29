# app/schemas/job_role.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JobRoleBase(BaseModel):
    """Base schema for job role data."""
    name: str = Field(..., min_length=1, max_length=100, description="Job role name")
    description: Optional[str] = Field(None, max_length=1000, description="Job role description")
    category: Optional[str] = Field(None, max_length=50, description="Job role category (e.g., Engineering, Marketing)")

class JobRoleCreate(JobRoleBase):
    """Schema for creating a new job role."""
    is_active: bool = Field(True, description="Whether the job role is active")

class JobRoleUpdate(BaseModel):
    """Schema for updating job role information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Job role name")
    description: Optional[str] = Field(None, max_length=1000, description="Job role description")
    category: Optional[str] = Field(None, max_length=50, description="Job role category")
    is_active: Optional[bool] = Field(None, description="Whether the job role is active")

class JobRoleRead(JobRoleBase):
    """Schema for reading job role information."""
    id: str
    is_active: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class JobRoleListResponse(BaseModel):
    """Schema for job role list response."""
    job_roles: List[JobRoleRead]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool

class JobRoleSearchRequest(BaseModel):
    """Schema for job role search request."""
    name: Optional[str] = Field(None, description="Search by job role name")
    category: Optional[str] = Field(None, description="Search by category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")

class JobRoleResponse(BaseModel):
    """Schema for job role operation response."""
    message: str
    job_role: Optional[JobRoleRead] = None

class JobRoleSimple(BaseModel):
    """Simplified job role schema for dropdowns and basic selection."""
    id: str
    name: str
    category: Optional[str] = None
    
    class Config:
        from_attributes = True
