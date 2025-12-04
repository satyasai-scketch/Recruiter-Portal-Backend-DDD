from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.ai_persona import AIGeneratedPersonaModel, PersonaAISourceMappingModel

class SQLAlchemyAIPersonaRepository:
    """Repository for AI persona templates"""
    
    def create(self, db: Session, model: AIGeneratedPersonaModel) -> AIGeneratedPersonaModel:
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    def update(self, db: Session, model: AIGeneratedPersonaModel) -> AIGeneratedPersonaModel:
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def get(self, db: Session, ai_persona_id: str) -> Optional[AIGeneratedPersonaModel]:
        return db.query(AIGeneratedPersonaModel).filter(
            AIGeneratedPersonaModel.id == ai_persona_id
        ).first()
    
    def get_by_jd(self, db: Session, jd_id: str) -> Optional[AIGeneratedPersonaModel]:
        return db.query(AIGeneratedPersonaModel).filter(
            AIGeneratedPersonaModel.job_description_id == jd_id
        ).first()
    
    def list_by_job_family(self, db: Session, job_family: str, seniority: Optional[str] = None) -> List[AIGeneratedPersonaModel]:
        query = db.query(AIGeneratedPersonaModel).filter(
            AIGeneratedPersonaModel.job_family == job_family
        )
        if seniority:
            query = query.filter(AIGeneratedPersonaModel.seniority_level == seniority)
        return query.all()
    
    def count(self, db: Session) -> int:
        return db.query(AIGeneratedPersonaModel).count()


class SQLAlchemyPersonaAIMappingRepository:
    """Repository for persona-AI mappings"""
    
    def create(self, db: Session, model: PersonaAISourceMappingModel) -> PersonaAISourceMappingModel:
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    
    def get_by_persona(self, db: Session, persona_id: str) -> Optional[PersonaAISourceMappingModel]:
        return db.query(PersonaAISourceMappingModel).filter(
            PersonaAISourceMappingModel.persona_id == persona_id
        ).first()
    
    def get_ai_source(self, db: Session, persona_id: str) -> Optional[AIGeneratedPersonaModel]:
        """Get the AI template that was source for a persona"""
        mapping = self.get_by_persona(db, persona_id)
        if not mapping:
            return None
        return db.query(AIGeneratedPersonaModel).filter(
            AIGeneratedPersonaModel.id == mapping.ai_persona_id
        ).first()