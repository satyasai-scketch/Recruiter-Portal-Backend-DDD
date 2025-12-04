from typing import Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models.ai_persona import AIGeneratedPersonaModel, PersonaAISourceMappingModel
from app.repositories.ai_persona_repo import (
    SQLAlchemyAIPersonaRepository,
    SQLAlchemyPersonaAIMappingRepository
)

class AIPersonaService:
    """Service for AI persona template management"""
    
    def __init__(
        self, 
        repo: Optional[SQLAlchemyAIPersonaRepository] = None,
        mapping_repo: Optional[SQLAlchemyPersonaAIMappingRepository] = None
    ):
        self.repo = repo or SQLAlchemyAIPersonaRepository()
        self.mapping_repo = mapping_repo or SQLAlchemyPersonaAIMappingRepository()
    
    def create(self, db: Session, data: Dict[str, Any]) -> AIGeneratedPersonaModel:
        """Create AI persona template"""
        existing = self.get_by_jd(db, data['job_description_id'])

        if existing:
            # Update all fields
            existing.persona_json = data['persona_json']
            existing.analysis_json = data['analysis_json']
            existing.weights_data_json = data['weights_data_json']
            existing.job_title = data.get('job_title')
            existing.job_family = data.get('job_family')
            existing.seniority_level = data.get('seniority_level')
            existing.technical_intensity = data.get('technical_intensity')
            existing.jd_text = data['jd_text'] 
            existing.model_used = data.get('model_used')
            existing.generation_cost = data.get('generation_cost')
            existing.generation_time_seconds = data.get('generation_time_seconds')

            return self.repo.update(db, existing)
        model = AIGeneratedPersonaModel(
            id=str(uuid4()),
            job_description_id=data['job_description_id'],
            persona_json=data['persona_json'],
            analysis_json=data['analysis_json'],
            weights_data_json=data['weights_data_json'],
            job_title=data.get('job_title'),
            job_family=data.get('job_family'),
            seniority_level=data.get('seniority_level'),
            technical_intensity=data.get('technical_intensity'),
            jd_text=data['jd_text'],
            model_used=data.get('model_used'),
            generation_cost=data.get('generation_cost'),
            generation_time_seconds=data.get('generation_time_seconds')
        )
        return self.repo.create(db, model)
    
    def get_by_id(self, db: Session, ai_persona_id: str) -> Optional[AIGeneratedPersonaModel]:
        return self.repo.get(db, ai_persona_id)
    
    def get_by_jd(self, db: Session, jd_id: str) -> Optional[AIGeneratedPersonaModel]:
        return self.repo.get_by_jd(db, jd_id)
    
    def create_mapping(
        self, 
        db: Session, 
        persona_id: str, 
        ai_persona_id: str,
        generation_method: str,
        similarity_score: Optional[float] = None
    ) -> PersonaAISourceMappingModel:
        """Link a user persona to its AI source"""
        model = PersonaAISourceMappingModel(
            id=str(uuid4()),
            persona_id=persona_id,
            ai_persona_id=ai_persona_id,
            generation_method=generation_method,
            similarity_score=similarity_score
        )
        return self.mapping_repo.create(db, model)
    
    def get_ai_source_for_persona(self, db: Session, persona_id: str) -> Optional[AIGeneratedPersonaModel]:
        """Get AI template that was source for a persona"""
        return self.mapping_repo.get_ai_source(db, persona_id)