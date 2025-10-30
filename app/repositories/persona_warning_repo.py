from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.persona import PersonaWeightWarningModel


class PersonaWarningRepository:
    """Repository interface for PersonaWeightWarning"""
    
    def get(self, db: Session, warning_id: str) -> Optional[PersonaWeightWarningModel]:
        raise NotImplementedError
    
    def create(self, db: Session, warning: PersonaWeightWarningModel) -> PersonaWeightWarningModel:
        raise NotImplementedError
    
    def get_by_entity(
        self, 
        db: Session, 
        persona_id: str, 
        entity_type: str, 
        entity_name: str
    ) -> Optional[PersonaWeightWarningModel]:
        raise NotImplementedError
    
    def list_by_persona(self, db: Session, persona_id: str) -> List[PersonaWeightWarningModel]:
        raise NotImplementedError
    
    def bulk_create(self, db: Session, warnings: List[PersonaWeightWarningModel]) -> List[PersonaWeightWarningModel]:
        raise NotImplementedError
    
    def update_persona_id(self, db: Session, old_persona_id: str, new_persona_id: str) -> int:
        """Update persona_id for warnings (when preview becomes saved)"""
        raise NotImplementedError


class SQLAlchemyPersonaWarningRepository(PersonaWarningRepository):
    """SQLAlchemy implementation of PersonaWarningRepository"""
    
    def get(self, db: Session, warning_id: str) -> Optional[PersonaWeightWarningModel]:
        return db.query(PersonaWeightWarningModel).filter(
            PersonaWeightWarningModel.id == warning_id
        ).first()
    
    def create(self, db: Session, warning: PersonaWeightWarningModel) -> PersonaWeightWarningModel:
        db.add(warning)
        db.commit()
        db.refresh(warning)
        return warning
    
    def get_by_entity(
        self, 
        db: Session, 
        persona_id: str, 
        entity_type: str, 
        entity_name: str
    ) -> Optional[PersonaWeightWarningModel]:
        return db.query(PersonaWeightWarningModel).filter(
            PersonaWeightWarningModel.persona_id == persona_id,
            PersonaWeightWarningModel.entity_type == entity_type,
            PersonaWeightWarningModel.entity_name == entity_name
        ).first()
    
    def list_by_persona(self, db: Session, persona_id: str) -> List[PersonaWeightWarningModel]:
        return db.query(PersonaWeightWarningModel).filter(
            PersonaWeightWarningModel.persona_id == persona_id
        ).order_by(PersonaWeightWarningModel.entity_type, PersonaWeightWarningModel.entity_name).all()
    
    def bulk_create(self, db: Session, warnings: List[PersonaWeightWarningModel]) -> List[PersonaWeightWarningModel]:
        """Create multiple warnings in one transaction"""
        db.add_all(warnings)
        db.commit()
        for warning in warnings:
            db.refresh(warning)
        return warnings
    
    def update_persona_id(self, db: Session, old_persona_id: str, new_persona_id: str) -> int:
        """Update persona_id when preview persona is saved"""
        updated_count = db.query(PersonaWeightWarningModel).filter(
            PersonaWeightWarningModel.persona_id == old_persona_id
        ).update({"persona_id": new_persona_id})
        db.commit()
        return updated_count