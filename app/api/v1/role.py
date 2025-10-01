# app/api/v1/role.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4

from app.api.deps import get_db, get_current_user
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleRead,
    RoleListResponse
)
from app.repositories.role_repo import RoleRepository
from app.db.models.user import UserModel

router = APIRouter()

@router.post("/", response_model=RoleRead, summary="Create Role")
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new user role.
    
    - **name**: Role name (required)
    """
    try:
        role_repo = RoleRepository()
        
        # Check if role with same name already exists
        existing_role = role_repo.get_by_name(db, role_data.name)
        if existing_role:
            raise HTTPException(status_code=400, detail="Role with this name already exists")
        
        # Create role
        role_dict = {"id": str(uuid4()), "name": role_data.name}
        created_role = role_repo.create(db, role_dict)
        
        return RoleRead(
            id=created_role.id,
            name=created_role.name,
            created_at=getattr(created_role, 'created_at', None),
            updated_at=getattr(created_role, 'updated_at', None)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=RoleListResponse, summary="List Roles")
async def list_roles(
    skip: int = Query(0, ge=0, description="Number of roles to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of roles to return"),
    db: Session = Depends(get_db)
):
    """
    Get a list of all user roles with pagination.
    """
    try:
        role_repo = RoleRepository()
        roles = role_repo.get_all(db, skip=skip, limit=limit)
        
        # Convert to response format
        role_list = []
        for role in roles:
            role_list.append(RoleRead(
                id=role.id,
                name=role.name,
                created_at=getattr(role, 'created_at', None),
                updated_at=getattr(role, 'updated_at', None)
            ))
        
        return RoleListResponse(
            roles=role_list,
            total=len(role_list),
            skip=skip,
            limit=limit
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{role_id}", response_model=RoleRead, summary="Get Role by ID")
async def get_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a specific role by ID.
    """
    try:
        role_repo = RoleRepository()
        role = role_repo.get_by_id(db, role_id)
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return RoleRead(
            id=role.id,
            name=role.name,
            created_at=getattr(role, 'created_at', None),
            updated_at=getattr(role, 'updated_at', None)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{role_id}", response_model=RoleRead, summary="Update Role")
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update an existing role.
    
    - **name**: New role name
    """
    try:
        role_repo = RoleRepository()
        
        # Check if role exists
        existing_role = role_repo.get_by_id(db, role_id)
        if not existing_role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if another role with same name exists
        name_conflict = role_repo.get_by_name(db, role_data.name)
        if name_conflict and name_conflict.id != role_id:
            raise HTTPException(status_code=400, detail="Role with this name already exists")
        
        # Update role
        updated_role = role_repo.update(db, role_id, {"name": role_data.name})
        
        return RoleRead(
            id=updated_role.id,
            name=updated_role.name,
            created_at=getattr(updated_role, 'created_at', None),
            updated_at=getattr(updated_role, 'updated_at', None)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{role_id}", summary="Delete Role")
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a role.
    """
    try:
        role_repo = RoleRepository()
        
        # Check if role exists
        if not role_repo.exists(db, role_id):
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if any users are using this role
        users_with_role = db.query(UserModel).filter(UserModel.role_id == role_id).count()
        if users_with_role > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete role. {users_with_role} user(s) are currently using this role."
            )
        
        # Delete role
        success = role_repo.delete(db, role_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete role")
        
        return {"message": "Role deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
