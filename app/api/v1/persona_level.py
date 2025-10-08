from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import SQLAlchemyError


from app.utils.error_handlers import handle_service_errors, rollback_on_error
from app.api.deps import db_session
from app.schemas.persona import PersonaLevelCreate, PersonaLevelUpdate, PersonaLevelRead
from app.services.persona_level_service import PersonaLevelService
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.persona_level_commands import CreatePersonaLevel, UpdatePersonaLevel, DeletePersonaLevel
from app.cqrs.queries.persona_level_queries import GetPersonaLevel, GetPersonaLevelByName, ListPersonaLevels, ListAllPersonaLevels, GetPersonaLevelByPosition

router = APIRouter()


@router.post("/", response_model=PersonaLevelRead, status_code=status.HTTP_201_CREATED, summary="Create a new persona level")
async def create_persona_level(
    payload: PersonaLevelCreate, 
    db: Session = Depends(db_session)
):
    """Create a new persona level."""
    try:
        level = handle_command(db, CreatePersonaLevel(payload))
        return PersonaLevelRead.model_validate(level)
    except (ValueError, SQLAlchemyError) as e:
        if isinstance(e, SQLAlchemyError):
            rollback_on_error(db)
        raise handle_service_errors(e)


@router.get("/", response_model=List[PersonaLevelRead], summary="List all persona levels")
async def list_persona_levels(
    sort_by_position: bool = True,
    db: Session = Depends(db_session)
):
    """List all persona levels, optionally sorted by position."""
    levels = handle_query(db, ListPersonaLevels(sort_by_position=sort_by_position))
    return [PersonaLevelRead.model_validate(level) for level in levels]


@router.get("/{level_id}", response_model=PersonaLevelRead, summary="Get persona level by ID")
async def get_persona_level(
    level_id: str,
    db: Session = Depends(db_session)
):
    """Get a specific persona level by ID."""
    level = handle_query(db, GetPersonaLevel(level_id))
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
    level = handle_query(db, GetPersonaLevelByName(name))
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
        level = handle_command(db, UpdatePersonaLevel(level_id, payload))
        if not level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Persona level with ID '{level_id}' not found"
            )
        return PersonaLevelRead.model_validate(level)
    except (ValueError, SQLAlchemyError) as e:
        if isinstance(e, SQLAlchemyError):
            rollback_on_error(db)
        raise handle_service_errors(e)


@router.delete("/{level_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete persona level")
async def delete_persona_level(
    level_id: str,
    db: Session = Depends(db_session)
):
    """Delete a persona level."""
    success = handle_command(db, DeletePersonaLevel(level_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Persona level with ID '{level_id}' not found"
        )
    return {"message": "Persona level deleted successfully"}


@router.get("/count/total", response_model=dict, summary="Get total count of persona levels")
async def get_persona_levels_count(db: Session = Depends(db_session)):
    """Get the total count of persona levels."""
    count = handle_query(db, ListAllPersonaLevels())
    return {"total_count": count}
