from __future__ import annotations

from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.job_description import JobDescriptionModel
from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
from app.domain.job_description import services as jd_domain_services
from app.events.event_bus import event_bus
from app.events.jd_events import JDCreatedEvent, JDFinalizedEvent


class JDService:
	"""Orchestrates Job Description workflows at the application layer."""

	def __init__(self, repo: Optional[SQLAlchemyJobDescriptionRepository] = None):
		self.repo = repo or SQLAlchemyJobDescriptionRepository()

	def create(self, db: Session, data: dict) -> JobDescriptionModel:
		"""Create a JD record after validating via the domain factory."""
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
			company_id=jd_agg.company.company_id if jd_agg.company else None,
			notes=jd_agg.notes.text if jd_agg.notes else None,
			tags=jd_agg.tags,
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
