from __future__ import annotations

from typing import Optional, Sequence
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.job_description import JobDescriptionModel
from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
from app.domain.job_description import services as jd_domain_services
from app.domain.job_description.entities import DocumentMetadata
from app.events.event_bus import event_bus
from app.events.jd_events import JDCreatedEvent, JDFinalizedEvent
from app.utils.document_parser import extract_job_description_text, DocumentParseError


class JDService:
	"""Orchestrates Job Description workflows at the application layer."""

	def __init__(self, repo: Optional[SQLAlchemyJobDescriptionRepository] = None):
		self.repo = repo or SQLAlchemyJobDescriptionRepository()

	def get_by_id(self, db: Session, jd_id: str) -> Optional[JobDescriptionModel]:
		return self.repo.get(db, jd_id)

	def list_all(self, db: Session) -> Sequence[JobDescriptionModel]:
		return self.repo.list_all(db)

	def list_by_creator(self, db: Session, user_id: str) -> Sequence[JobDescriptionModel]:
		return self.repo.list_by_creator(db, user_id)

	def create(self, db: Session, data: dict) -> JobDescriptionModel:
		jd_agg = jd_domain_services.create_job_description(
			id=str(uuid4()),
			title=data["title"],
			role_name=data["role"],
			original_text=data["original_text"],
			company_id=data.get("company_id"),
			notes_text=data.get("notes"),
			tags=data.get("tags") or [],
		)
		model = JobDescriptionModel(
				id=jd_agg.id,
				title=jd_agg.title,
				role=jd_agg.role.name,
				original_text=jd_agg.original_text,
				refined_text=jd_agg.refined_text,
				selected_version=data.get("selected_version"),
				selected_text=data.get("selected_text"),
				selected_edited=bool(data.get("selected_edited")) if data.get("selected_edited") is not None else False,
				company_id=jd_agg.company.company_id if jd_agg.company else None,
				notes=jd_agg.notes.text if jd_agg.notes else None,
				tags=jd_agg.tags,
				created_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
				updated_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
			)
		created = self.repo.create(db, model)
		event_bus.publish_event(JDCreatedEvent(id=created.id, title=created.title, role=created.role, company_id=created.company_id))
		return created

	def prepare_refinement_brief(self, db: Session, jd_id: str, required_sections: list[str], template_text: Optional[str] = None) -> dict:
		"""Prepare a domain refinement brief for the given JD id."""
		model = self.repo.get(db, jd_id)
		if not model:
			raise ValueError("Job description not found")
		jd_agg = jd_domain_services.create_job_description(
			id=model.id,
			title=model.title,
			role_name=model.role,
			original_text=model.original_text,
			company_id=model.company_id,
			notes_text=model.notes,
			tags=model.tags or [],
		)
		return jd_domain_services.prepare_refinement_brief(jd_agg, required_sections, template_text)

	def apply_refinement(self, db: Session, jd_id: str, refined_text: str) -> JobDescriptionModel:
		"""Apply refined text to JD using domain rules and persist the update."""
		model = self.repo.get(db, jd_id)
		if not model:
			raise ValueError("Job description not found")
		jd_agg = jd_domain_services.create_job_description(
			id=model.id,
			title=model.title,
			role_name=model.role,
			original_text=model.original_text,
			company_id=model.company_id,
			notes_text=model.notes,
			tags=model.tags or [],
		)
		updated_agg = jd_domain_services.apply_refinement(jd_agg, refined_text)
		model.refined_text = updated_agg.refined_text
		updated = self.repo.update(db, model)
		event_bus.publish_event(JDFinalizedEvent(id=updated.id, selected_text=updated.refined_text or updated.original_text))
		return updated

	def update_partial(self, db: Session, jd_id: str, fields: dict, updated_by: str = None) -> JobDescriptionModel:
		model = self.repo.get(db, jd_id)
		if not model:
			raise ValueError("Job description not found")
		# Directly assign values provided by frontend without inference
		if "selected_text" in fields:
			model.selected_text = fields["selected_text"]
		if "selected_version" in fields:
			model.selected_version = fields["selected_version"]
		if "selected_edited" in fields:
			model.selected_edited = bool(fields["selected_edited"]) if fields["selected_edited"] is not None else model.selected_edited
		if "title" in fields and fields["title"]:
			model.title = fields["title"].strip()
		if "notes" in fields:
			model.notes = fields["notes"]
		if "tags" in fields and isinstance(fields["tags"], list):
			model.tags = fields["tags"]
		# Update audit fields
		if updated_by:
			model.updated_by = updated_by
		return self.repo.update(db, model)

	def create_from_document(self, db: Session, data: dict, file_content: bytes, filename: str) -> JobDescriptionModel:
		"""Create a job description from an uploaded document."""
		try:
			# Extract text from document
			extraction_result = extract_job_description_text(filename, file_content)
			
			# Create document metadata
			doc_metadata = DocumentMetadata(
				filename=extraction_result['original_filename'],
				file_size=extraction_result['file_size'],
				file_extension=extraction_result['file_extension'],
				word_count=extraction_result['word_count'],
				character_count=extraction_result['character_count']
			)
			
			# Create domain aggregate
			jd_agg = jd_domain_services.create_job_description(
				id=str(uuid4()),
				title=data["title"],
				role_name=data["role"],
				original_text=extraction_result['extracted_text'],
				company_id=data.get("company_id"),
				notes_text=data.get("notes"),
				tags=data.get("tags") or [],
				document_metadata=doc_metadata
			)
			
			# Create model
			model = JobDescriptionModel(
				id=jd_agg.id,
				title=jd_agg.title,
				role=jd_agg.role.name,
				original_text=jd_agg.original_text,
				refined_text=jd_agg.refined_text,
				selected_version=data.get("selected_version"),
				selected_text=data.get("selected_text"),
				selected_edited=bool(data.get("selected_edited")) if data.get("selected_edited") is not None else False,
				company_id=jd_agg.company.company_id if jd_agg.company else None,
				notes=jd_agg.notes.text if jd_agg.notes else None,
				tags=jd_agg.tags,
				created_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
				updated_by=data.get("created_by") or data.get("user_id") or data.get("owner_id") or "",
				# Document metadata
				original_document_filename=doc_metadata.filename,
				original_document_size=str(doc_metadata.file_size),
				original_document_extension=doc_metadata.file_extension,
				document_word_count=str(doc_metadata.word_count),
				document_character_count=str(doc_metadata.character_count)
			)
			
			created = self.repo.create(db, model)
			event_bus.publish_event(JDCreatedEvent(
				id=created.id, 
				title=created.title, 
				role=created.role, 
				company_id=created.company_id
			))
			
			return created
			
		except DocumentParseError as e:
			raise ValueError(f"Document parsing failed: {str(e)}")
		except Exception as e:
			raise ValueError(f"Failed to create job description from document: {str(e)}")
