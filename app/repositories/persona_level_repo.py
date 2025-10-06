from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.db.models.persona import PersonaLevelModel


class PersonaLevelRepository:
    """Repository interface for PersonaLevel operations."""

    def get(self, db: Session, level_id: str) -> Optional[PersonaLevelModel]:
        raise NotImplementedError

    def get_by_name(self, db: Session, name: str) -> Optional[PersonaLevelModel]:
        raise NotImplementedError

    def create(self, db: Session, level: PersonaLevelModel) -> PersonaLevelModel:
        raise NotImplementedError

    def update(self, db: Session, level: PersonaLevelModel) -> PersonaLevelModel:
        raise NotImplementedError

    def delete(self, db: Session, level_id: str) -> bool:
        raise NotImplementedError

    def list_all(self, db: Session) -> Sequence[PersonaLevelModel]:
        raise NotImplementedError

    def list_by_position(self, db: Session) -> Sequence[PersonaLevelModel]:
        raise NotImplementedError


class SQLAlchemyPersonaLevelRepository(PersonaLevelRepository):
    """SQLAlchemy-backed implementation of PersonaLevelRepository."""

    def get(self, db: Session, level_id: str) -> Optional[PersonaLevelModel]:
        return db.query(PersonaLevelModel).filter(PersonaLevelModel.id == level_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[PersonaLevelModel]:
        return db.query(PersonaLevelModel).filter(PersonaLevelModel.name == name).first()

    def create(self, db: Session, level: PersonaLevelModel) -> PersonaLevelModel:
        db.add(level)
        db.commit()
        db.refresh(level)
        return level

    def update(self, db: Session, level: PersonaLevelModel) -> PersonaLevelModel:
        db.add(level)
        db.commit()
        db.refresh(level)
        return level

    def delete(self, db: Session, level_id: str) -> bool:
        level = db.query(PersonaLevelModel).filter(PersonaLevelModel.id == level_id).first()
        if level:
            db.delete(level)
            db.commit()
            return True
        return False

    def list_all(self, db: Session) -> Sequence[PersonaLevelModel]:
        return db.query(PersonaLevelModel).all()

    def list_by_position(self, db: Session) -> Sequence[PersonaLevelModel]:
        return (
            db.query(PersonaLevelModel)
            .order_by(asc(PersonaLevelModel.position), asc(PersonaLevelModel.name))
            .all()
        )
