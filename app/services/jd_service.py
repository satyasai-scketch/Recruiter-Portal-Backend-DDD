# app/services/jd_service_updated.py
from typing import Sequence, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.job_description import JobDescriptionModel
from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
from app.domain.job_description import services as jd_domain_services
from app.domain.job_description.entities import DocumentMetadata
from app.utils.document_parser import extract_job_description_text
from app.events.jd_events import JDCreatedEvent, JDUpdatedEvent
from app.events.event_bus import event_bus

class JDService:
    """Application service for Job Description operations."""

    def __init__(self):
        self.repo = SQLAlchemyJobDescriptionRepository()

    def list_by_creator(self, db: Session, user_id: str) -> Sequence[JobDescriptionModel]:
        return self.repo.list_by_creator(db, user_id)
    
    def list_all(self, db: Session) -> Sequence[JobDescriptionModel]:
        return self.repo.list_all(db)

    def create(self, db: Session, data: dict) -> JobDescriptionModel:
        """Create a new job description with role_id."""
        model = JobDescriptionModel(
            id=str(uuid4()),
            title=data["title"],
            role_id=data["role_id"],
            original_text=data["original_text"],
            refined_text=None,
            selected_version=data.get("selected_version"),
            selected_text=data.get("selected_text"),
            selected_edited=bool(data.get("selected_edited")) if data.get("selected_edited") is not None else False,
            company_id=data.get("company_id"),
            notes=data.get("notes"),
            tags=data.get("tags") or [],
            created_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
            updated_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
        )
        created = self.repo.create(db, model)
        event_bus.publish_event(JDCreatedEvent(id=created.id, title=created.title, role=created.role_id, company_id=created.company_id))
        return created

    def create_from_document(self, db: Session, data: dict, file_content: bytes, filename: str) -> JobDescriptionModel:
        """Create a job description from uploaded document."""
        # Extract text and metadata from document
        extraction_result = extract_job_description_text(filename, file_content)
        extracted_text = extraction_result['extracted_text']
        metadata = extraction_result
        
        # Create job description model
        model = JobDescriptionModel(
            id=str(uuid4()),
            title=data["title"],
            role_id=data["role_id"],
            original_text=extracted_text,
            refined_text=None,
            company_id=data.get("company_id"),
            notes=data.get("notes"),
            tags=data.get("tags") or [],
            created_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
            updated_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
            # Document metadata
            original_document_filename=metadata.get("original_filename"),
            original_document_size=str(metadata.get("file_size")),
            original_document_extension=metadata.get("file_extension"),
            document_word_count=str(metadata.get("word_count")),
            document_character_count=str(metadata.get("character_count")),
        )
        
        created = self.repo.create(db, model)
        event_bus.publish_event(JDCreatedEvent(id=created.id, title=created.title, role=created.role_id, company_id=created.company_id))
        return created

    def get_by_id(self, db: Session, jd_id: str) -> Optional[JobDescriptionModel]:
        return self.repo.get(db, jd_id)

    def prepare_refinement_brief(self, db: Session, jd_id: str, required_sections: list[str], template_text: Optional[str] = None) -> dict:
        """Prepare AI refinement brief for job description."""
        jd = self.get_by_id(db, jd_id)
        if not jd:
            raise ValueError("Job description not found")
        
        # For now, return a simple structure
        # In the future, this would integrate with AI services
        return {
            "jd_id": jd_id,
            "title": jd.title,
            "original_text": jd.original_text,
            "required_sections": required_sections,
            "template_text": template_text,
            "refinement_instructions": "Please refine the job description based on the requirements."
        }

    def apply_refinement(self, db: Session, jd_id: str, refined_text: str) -> JobDescriptionModel:
        """Apply AI refinement to job description."""
        jd = self.get_by_id(db, jd_id)
        if not jd:
            raise ValueError("Job description not found")
        
        jd.refined_text = refined_text
        updated = self.repo.update(db, jd)
        event_bus.publish_event(JDUpdatedEvent(id=updated.id, title=updated.title, role=updated.role_id))
        return updated

    def update_partial(self, db: Session, jd_id: str, fields: dict, updated_by: str) -> Optional[JobDescriptionModel]:
        """Update specific fields of a job description."""
        jd = self.get_by_id(db, jd_id)
        if not jd:
            return None
        
        # Update fields
        for key, value in fields.items():
            if hasattr(jd, key):
                setattr(jd, key, value)
        
        jd.updated_by = updated_by
        updated = self.repo.update(db, jd)
        event_bus.publish_event(JDUpdatedEvent(id=updated.id, title=updated.title, role=updated.role_id))
        return updated
