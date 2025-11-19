# app/services/jd_service_updated.py
from typing import Sequence, Optional, Set
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.job_description import JobDescriptionModel
from app.db.models.persona import PersonaModel
from app.db.models.jd_hiring_manager import JDHiringManagerMappingModel
from app.db.models.user import UserModel
from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
from app.domain.job_description import services as jd_domain_services
from app.domain.job_description.entities import DocumentMetadata
from app.utils.document_parser import extract_job_description_text
from app.events.jd_events import JDCreatedEvent, JDUpdatedEvent
from app.events.event_bus import event_bus
from app.services.jd_refinement.refinement_service import JDRefinementService
from app.repositories.company_repo import CompanyRepository
from app.utils.jd_diff import JDDiffGenerator
from app.utils.jd_inline_diff import JDInlineDiffGenerator
from types import SimpleNamespace

class JDService:
    """Application service for Job Description operations."""

    def __init__(self):
        self.repo = SQLAlchemyJobDescriptionRepository()
        self.company_repo = CompanyRepository()  # Add this
        self.refinement_service = JDRefinementService()

    def list_by_creator(self, db: Session, user_id: str) -> Sequence[JobDescriptionModel]:
        return self.repo.list_by_creator(db, user_id)
    
    def list_by_role_id(self, db: Session, role_id: str, skip: int = 0, limit: int = 100, optimized: bool = True) -> Sequence[JobDescriptionModel]:
        """List job descriptions filtered by role_id."""
        return self.repo.list_by_role_id(db, role_id, skip, limit, optimized)
    
    def list_all(self, db: Session, skip: int = 0, limit: int = 100, user: Optional[UserModel] = None) -> Sequence[JobDescriptionModel]:
        """List all JDs, optionally filtered by user access."""
        if user is not None:
            return self.repo.list_accessible(db, user, skip, limit)
        return self.repo.list_all(db, skip, limit)
    
    def list_all_optimized(self, db: Session, skip: int = 0, limit: int = 100, user: Optional[UserModel] = None) -> Sequence[JobDescriptionModel]:
        """Optimized list that excludes large text fields for better performance."""
        if user is not None:
            return self.repo.list_accessible(db, user, skip, limit)
        return self.repo.list_all_optimized(db, skip, limit)

    def count(self, db: Session, user: Optional[UserModel] = None) -> int:
        """Count all job descriptions, optionally filtered by user access."""
        if user is not None:
            return self.repo.count_accessible(db, user)
        return self.repo.count(db)

    def _create_hiring_manager_mappings(self, db: Session, jd_id: str, hiring_manager_ids: list[str], created_by: str) -> None:
        """Create hiring manager mappings for a job description."""
        if not hiring_manager_ids:
            return
        
        for hm_id in hiring_manager_ids:
            mapping = JDHiringManagerMappingModel(
                id=str(uuid4()),
                job_description_id=jd_id,
                hiring_manager_id=hm_id,
                created_by=created_by
            )
            db.add(mapping)
        db.commit()

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
        
        # Create hiring manager mappings if provided
        hiring_manager_ids = data.get("hiring_manager_ids", [])
        if hiring_manager_ids:
            self._create_hiring_manager_mappings(db, created.id, hiring_manager_ids, created.created_by)
        
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
        
        # Create hiring manager mappings if provided
        hiring_manager_ids = data.get("hiring_manager_ids", [])
        if hiring_manager_ids:
            self._create_hiring_manager_mappings(db, created.id, hiring_manager_ids, created.created_by)
        
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
    async def apply_refinement_with_ai(
        self, 
        db: Session, 
        jd_id: str, 
        role: str,
        company_id: str,
        methodology: str = "direct",
        min_similarity: float = 0.7
    ) -> tuple:
        """Apply AI refinement to job description."""
        
        # Get JD
        jd = self.get_by_id(db, jd_id)
        if not jd:
            raise ValueError("Job description not found")

        if company_id:
            company = self.company_repo.get_by_id(db, company_id)
            if company:
                company_info = SimpleNamespace(
                    name=company.name,
                    website_url=company.website_url,
                    contact_number=company.contact_number,
                    email_address=company.email_address,
                    about_company=company.about_company,
                    address=SimpleNamespace(
                        street=company.address.street if company.address else None,
                        city=company.address.city if company.address else None,
                        state=company.address.state if company.address else None,
                        country=company.address.country if company.address else None,
                        pincode=company.address.pincode if company.address else None,
                    ) if hasattr(company, 'address') and company.address else SimpleNamespace(),
                    social_media=SimpleNamespace(
                        twitter_link=company.social_media.twitter_link if company.social_media else None,
                        instagram_link=company.social_media.instagram_link if company.social_media else None,
                        facebook_link=company.social_media.facebook_link if company.social_media else None,
                    ) if hasattr(company, 'social_media') and company.social_media else SimpleNamespace()
                )
            else:
                # Company ID provided but not found - use generic
                company_info = SimpleNamespace(name="Not specified")
        else:
            # No company ID - use generic
            company_info = SimpleNamespace(name="Not specified")
        
        # Get company - FIXED: use get_by_id instead of get
        # company = self.company_repo.get_by_id(db, company_id)
        # if not company:
        #     raise ValueError(f"Company {company_id} not found")
        
        # # Convert company model to simple object
        # from types import SimpleNamespace
        # company_info = SimpleNamespace(
        #     name=company.name,
        #     website_url=company.website_url,
        #     contact_number=company.contact_number,
        #     email_address=company.email_address,
        #     about_company=company.about_company,
        #     address=SimpleNamespace(
        #         street=company.address.street if company.address else None,
        #         city=company.address.city if company.address else None,
        #         state=company.address.state if company.address else None,
        #         country=company.address.country if company.address else None,
        #         pincode=company.address.pincode if company.address else None,
        #     ) if hasattr(company, 'address') and company.address else SimpleNamespace(),
        #     social_media=SimpleNamespace(
        #         twitter_link=company.social_media.twitter_link if company.social_media else None,
        #         instagram_link=company.social_media.instagram_link if company.social_media else None,
        #         facebook_link=company.social_media.facebook_link if company.social_media else None,
        #     ) if hasattr(company, 'social_media') and company.social_media else SimpleNamespace()
        # )
        
        # Use AI service
        if methodology == "template_based":
            result = await self.refinement_service.refine_with_template(
                jd_text=jd.original_text,
                role=role,
                company_info=company_info,
                min_similarity=min_similarity
            )
        else:
            result = await self.refinement_service.refine_direct(
                notes=jd.notes or "",
                jd_text=jd.original_text,
                role=role,
                company_info=company_info
            )
        
        # Update JD with refined text
        jd.refined_text = result.refined_text
        updated = self.repo.update(db, jd)
        
        from app.events.jd_events import JDUpdatedEvent
        from app.events.event_bus import event_bus
        event_bus.publish_event(JDUpdatedEvent(
            id=updated.id, 
            title=updated.title, 
            role=updated.role_id
        ))
        
        return updated, result
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
    
    def get_jd_diff(self, db: Session, jd_id: str, diff_format: str = "table") -> dict:
        """
        Get diff between original and refined JD.
        
        Args:
            db: Database session
            jd_id: Job description ID
            diff_format: "table" (default), "inline", or "simple"
            
        Returns:
            Dict with diff HTML and statistics
        """
        jd = self.get_by_id(db, jd_id)
        if not jd:
            raise ValueError("Job description not found")
        
        if not jd.refined_text:
            raise ValueError("JD has not been refined yet")
        
        original = jd.original_text or ""
        refined = jd.refined_text or ""
        
        # Generate diff based on format
        if diff_format == "inline":
            diff_html, stats = JDDiffGenerator.generate_inline_diff(original, refined)
        elif diff_format == "simple":
            diff_html = JDDiffGenerator.generate_simple_diff(original, refined)
            stats = JDDiffGenerator._calculate_stats(original, refined)
        else:  # table (default)
            diff_html, stats = JDDiffGenerator.generate_diff(original, refined)
        
        return {
            'jd_id': jd_id,
            'original_text': original,
            'refined_text': refined,
            'diff_html': diff_html,
            'stats': stats
        }
    
    def get_jd_inline_markup(self, db: Session, jd_id: str) -> dict:
        """
        Get separate marked-up texts for original and refined JD.
        
        Args:
            db: Database session
            jd_id: Job description ID
                
        Returns:
            Dict with marked up original and refined texts plus statistics
        """
        jd = self.get_by_id(db, jd_id)
        if not jd:
            raise ValueError("Job description not found")
                
        if not jd.refined_text:
            raise ValueError("JD has not been refined yet")
                
        original = jd.original_text or ""
        refined = jd.refined_text or ""
                
        # Generate inline markup using NEW class
        marked_original, marked_refined, stats = JDInlineDiffGenerator.generate_marked_texts(original, refined)
                
        return {
            'jd_id': jd_id,
            'original_text': marked_original,
            'refined_text': marked_refined,
            'stats': stats
        }
    
    def delete(self, db: Session, jd_id: str) -> dict:
        """
        Delete a job description and all associated data.
        
        This will:
        1. Delete all candidate scores evaluated against personas of this JD
        2. Delete all personas associated with this JD (cascade)
        3. Delete the job description itself
        
        Returns:
            Dictionary with deletion statistics
        """
        from app.db.models.score import CandidateScoreModel
        
        try:
            # Get the JD first to check if it exists
            jd = self.get_by_id(db, jd_id)
            if not jd:
                raise ValueError(f"Job description with ID '{jd_id}' not found")
            
            jd_title = jd.title  # Store title before deletion
            
            # Get all personas for this JD with all relationships loaded
            # Need to eagerly load all relationships to avoid lazy loading issues during deletion
            from sqlalchemy.orm import joinedload, selectinload
            from app.db.models.persona import (
                PersonaCategoryModel, PersonaSubcategoryModel, PersonaSkillsetModel,
                PersonaNotesModel, PersonaChangeLogModel
            )
            
            personas = (
                db.query(PersonaModel)
                .options(
                    selectinload(PersonaModel.categories).selectinload(PersonaCategoryModel.subcategories),
                    selectinload(PersonaModel.skillsets),
                    selectinload(PersonaModel.notes),
                    selectinload(PersonaModel.change_logs)
                )
                .filter(PersonaModel.job_description_id == jd_id)
                .all()
            )
            persona_ids = [p.id for p in personas]
            
            # Count and delete all candidate scores for these personas
            scores_count = 0
            if persona_ids:
                scores_count = db.query(CandidateScoreModel).filter(
                    CandidateScoreModel.persona_id.in_(persona_ids)
                ).count()
                
                # Delete all scores for these personas
                # Need to delete related data (stages, categories, insights) first
                # These cascade automatically, but we need to load them first for SQLite
                # DO NOT flush here - keep everything in one transaction for rollback safety
                if scores_count > 0:
                    # Get all scores to delete with their relationships
                    scores_to_delete = db.query(CandidateScoreModel).filter(
                        CandidateScoreModel.persona_id.in_(persona_ids)
                    ).all()
                    
                    # Delete each score individually to ensure cascades work properly
                    for score in scores_to_delete:
                        db.delete(score)
            
            # Manually delete personas using the same logic as delete_persona to avoid circular dependencies
            # This ensures all persona-related data is deleted before JD deletion
            # Use flush() only when necessary to clear foreign key references, but keep in transaction
            for persona in personas:
                # 1. First, clear all foreign key references that create circular dependencies
                # Flush after clearing references to ensure database state is updated
                for category in persona.categories:
                    # Clear notes_id reference in category
                    category.notes_id = None
                    
                    for subcategory in category.subcategories:
                        # Clear skillset_id reference in subcategory
                        subcategory.skillset_id = None
                
                # Flush once after clearing all references for this persona
                db.flush()
                
                # 2. Delete change logs first (no circular dependencies)
                for change_log in persona.change_logs:
                    db.delete(change_log)
                
                # 3. Delete notes (no circular dependencies after clearing references)
                for note in persona.notes:
                    db.delete(note)
                
                # 4. Delete skillsets (no circular dependencies after clearing references)
                for skillset in persona.skillsets:
                    db.delete(skillset)
                
                # 5. Delete subcategories (no circular dependencies after clearing references)
                for category in persona.categories:
                    for subcategory in category.subcategories:
                        db.delete(subcategory)
                
                # 6. Delete categories (no circular dependencies after clearing references)
                for category in persona.categories:
                    db.delete(category)
                
                # 7. Finally, delete the persona itself
                db.delete(persona)
            
            # Delete the JD
            # Use the jd we already fetched
            db.delete(jd)
            
            # Commit all deletions together in a single transaction
            # If any error occurs before this point, rollback will undo everything
            db.commit()
            
            # Return deletion statistics
            return {
                "jd_id": jd_id,
                "personas_deleted": len(persona_ids),
                "scores_deleted": scores_count,
                "message": f"Job description '{jd_title}' and all associated data deleted successfully"
            }
        except Exception as e:
            db.rollback()
            raise e