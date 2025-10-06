from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import db_session
from app.schemas.persona import PersonaLevelCreate, PersonaLevelUpdate, PersonaLevelRead
from app.services.persona_level_service import PersonaLevelService

router = APIRouter()


@router.post("/", response_model=PersonaLevelRead, status_code=status.HTTP_201_CREATED, summary="Create a new persona level")
async def create_persona_level(
    payload: PersonaLevelCreate, 
    db: Session = Depends(db_session)
):
    """Create a new persona level."""
    try:
        service = PersonaLevelService()
        level = service.create_level(db, payload)
        return PersonaLevelRead.model_validate(level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[PersonaLevelRead], summary="List all persona levels")
async def list_persona_levels(
    sort_by_position: bool = True,
    db: Session = Depends(db_session)
):
    """List all persona levels, optionally sorted by position."""
    service = PersonaLevelService()
    levels = service.list_levels(db, sort_by_position=sort_by_position)
    return [PersonaLevelRead.model_validate(level) for level in levels]


@router.get("/{level_id}", response_model=PersonaLevelRead, summary="Get persona level by ID")
async def get_persona_level(
    level_id: str,
    db: Session = Depends(db_session)
):
    """Get a specific persona level by ID."""
    service = PersonaLevelService()
    level = service.get_level(db, level_id)
    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Persona level with ID '{level_id}' not found"
        )
    return PersonaLevelRead.model_validate(level)


@router.get("/name/{name}", response_model=PersonaLevelRead, summary="Get persona level by name")
async def get_persona_level_by_name(
    name: str,
    db: Session = Depends(db_session)
):
    """Get a specific persona level by name."""
    service = PersonaLevelService()
    level = service.get_level_by_name(db, name)
    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Persona level with name '{name}' not found"
        )
    return PersonaLevelRead.model_validate(level)


@router.put("/{level_id}", response_model=PersonaLevelRead, summary="Update persona level")
async def update_persona_level(
    level_id: str,
    payload: PersonaLevelUpdate,
    db: Session = Depends(db_session)
):
    """Update a persona level."""
    try:
        service = PersonaLevelService()
        level = service.update_level(db, level_id, payload)
        if not level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Persona level with ID '{level_id}' not found"
            )
        return PersonaLevelRead.model_validate(level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{level_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete persona level")
async def delete_persona_level(
    level_id: str,
    db: Session = Depends(db_session)
):
    """Delete a persona level."""
    service = PersonaLevelService()
    success = service.delete_level(db, level_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Persona level with ID '{level_id}' not found"
        )


@router.get("/count/total", response_model=dict, summary="Get total count of persona levels")
async def get_persona_levels_count(db: Session = Depends(db_session)):
    """Get the total count of persona levels."""
    service = PersonaLevelService()
    count = service.get_levels_count(db)
    return {"total_count": count}
