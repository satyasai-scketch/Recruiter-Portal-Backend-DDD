from __future__ import annotations

from typing import Optional, Dict
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.persona import PersonaModel
from app.repositories.persona_repo import SQLAlchemyPersonaRepository
from app.domain.persona import services as persona_domain_services
from app.domain.persona.entities import WeightInterval
from app.events.event_bus import event_bus
from app.events.persona_events import PersonaCreatedEvent


class PersonaService:
	"""Orchestrates persona workflows at the application layer."""

	def __init__(self, repo: Optional[SQLAlchemyPersonaRepository] = None):
		self.repo = repo or SQLAlchemyPersonaRepository()

	def create(self, db: Session, data: dict) -> PersonaModel:
		"""Create a persona after validating via the domain factory."""
		intervals: Dict[str, WeightInterval] = {
			k: WeightInterval(v["min"], v["max"]) for k, v in (data.get("intervals") or {}).items()
		}
		persona_agg = persona_domain_services.create_persona(
			id=str(uuid4()),
			job_description_id=data["job_description_id"],
			name=data["name"],
			weights=data.get("weights"),
			intervals=intervals,
			normalize=True,
		)
		model = PersonaModel(
			id=persona_agg.id,
			job_description_id=persona_agg.job_description_id,
			name=persona_agg.name,
			weights=persona_agg.weights,
			intervals={k: {"min": v.min, "max": v.max} for k, v in persona_agg.intervals.items()},
		)
		created = self.repo.create(db, model)
		event_bus.publish_event(PersonaCreatedEvent(id=created.id, job_description_id=created.job_description_id, name=created.name))
		return created
