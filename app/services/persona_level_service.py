from __future__ import annotations

from typing import Optional, List
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.persona import PersonaLevelModel
from app.repositories.persona_level_repo import SQLAlchemyPersonaLevelRepository
from app.schemas.persona import PersonaLevelCreate, PersonaLevelUpdate


class PersonaLevelService:
    """Service layer for PersonaLevel business logic."""

    def __init__(self, repo: Optional[SQLAlchemyPersonaLevelRepository] = None):
        self.repo = repo or SQLAlchemyPersonaLevelRepository()

    def create_level(self, db: Session, data: PersonaLevelCreate) -> PersonaLevelModel:
        """Create a new persona level."""
        # Check if level with same name already exists
        existing = self.repo.get_by_name(db, data.name)
        if existing:
            raise ValueError(f"Persona level with name '{data.name}' already exists")

        level = PersonaLevelModel(
            id=str(uuid4()),
            name=data.name,
            position=data.position
        )
        
        return self.repo.create(db, level)

    def get_level(self, db: Session, level_id: str) -> Optional[PersonaLevelModel]:
        """Get a persona level by ID."""
        return self.repo.get(db, level_id)

    def get_level_by_name(self, db: Session, name: str) -> Optional[PersonaLevelModel]:
        """Get a persona level by name."""
        return self.repo.get_by_name(db, name)
    
    def get_level_by_position(self, db: Session, position: int) -> Optional[PersonaLevelModel]:
        """Get a persona level by position."""
        return self.repo.get_by_position(db, position)

    def update_level(self, db: Session, level_id: str, data: PersonaLevelUpdate) -> Optional[PersonaLevelModel]:
        """Update a persona level."""
        level = self.repo.get(db, level_id)
        if not level:
            return None

        # Check if name is being changed and if new name already exists
        if data.name and data.name != level.name:
            existing = self.repo.get_by_name(db, data.name)
            if existing:
                raise ValueError(f"Persona level with name '{data.name}' already exists")

        # Update fields
        if data.name is not None:
            level.name = data.name
        if data.position is not None:
            level.position = data.position

        return self.repo.update(db, level)

    def delete_level(self, db: Session, level_id: str) -> bool:
        """Delete a persona level."""
        # Check if level is being used by any subcategories
        from app.db.models.persona import PersonaSubcategoryModel
        from sqlalchemy.orm import Session
        
        # Note: We need to check if this level is referenced by any subcategories
        # For now, we'll allow deletion and let the database handle foreign key constraints
        return self.repo.delete(db, level_id)

    def list_levels(self, db: Session, sort_by_position: bool = True) -> List[PersonaLevelModel]:
        """List all persona levels."""
        if sort_by_position:
            return list(self.repo.list_by_position(db))
        return list(self.repo.list_all(db))

    def get_levels_count(self, db: Session) -> int:
        """Get the total count of persona levels."""
        return len(self.repo.list_all(db))
