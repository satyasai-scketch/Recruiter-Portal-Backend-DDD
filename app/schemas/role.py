# app/schemas/role.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    name: str = Field(min_length=1, max_length=50, description="Role name")

class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""
    name: str = Field(min_length=1, max_length=50, description="Role name")

class RoleRead(BaseModel):
    """Schema for reading role data."""
    id: str
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RoleSimple(BaseModel):
    """Simplified role schema for responses."""
    id: str
    name: str

class RoleListResponse(BaseModel):
    """Schema for role list response."""
    roles: list[RoleRead]
    total: int
    skip: int
    limit: int
