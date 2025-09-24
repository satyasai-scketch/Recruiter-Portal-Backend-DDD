from __future__ import annotations

from typing import Optional, Dict
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.persona import PersonaModel, PersonaCategoryModel, PersonaSubcategoryModel
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
		"""Create a persona after validating via the domain factory (legacy flat)."""
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
			intervals={k: {"min": v.min, "max": v.max} for k, v in (persona_agg.intervals or {}).items()},
		)
		created = self.repo.create(db, model)
		event_bus.publish_event(PersonaCreatedEvent(id=created.id, job_description_id=created.job_description_id, name=created.name))
		return created

	def _validate_nested_weights(self, data: dict) -> None:
		# Validate each category is 0..100 and sum subcategories to 100
		cat_total = 0
		for cat in data.get("categories", []) or []:
			w = int(cat.get("weight_percentage", 0))
			if not (0 <= w <= 100):
				raise ValueError(f"Category '{cat.get('name')}' weight_percentage must be 0..100")
			cat_total += w
			sub_total = 0
			for sub in cat.get("subcategories", []) or []:
				sw = int(sub.get("weight_percentage", 0))
				if not (0 <= sw <= 100):
					raise ValueError(f"Subcategory '{sub.get('name')}' weight_percentage must be 0..100")
				sub_total += sw
			if (cat.get("subcategories") or []) and sub_total != 100:
				raise ValueError(f"Subcategories of '{cat.get('name')}' must sum to 100 (got {sub_total})")
		if cat_total != 100:
			raise ValueError(f"All category weight_percentage must sum to 100 (got {cat_total})")

	def create_nested(self, db: Session, data: dict) -> PersonaModel:
		"""Create a nested persona graph (persona + categories + subcategories)."""
		self._validate_nested_weights(data)
		persona_id = str(uuid4())
		persona = PersonaModel(
			id=persona_id,
			job_description_id=data["job_description_id"],
			name=data["name"],
			weights=None,  # deprecated
			intervals=None,  # deprecated
		)
		created = self.repo.create(db, persona)

		for cat in data.get("categories", []) or []:
			cat_id = str(uuid4())
			cat_model = PersonaCategoryModel(
				id=cat_id,
				persona_id=created.id,
				name=cat["name"],
				weight_percentage=int(cat["weight_percentage"]),
			)
			self.repo.add_category(db, cat_model)

			for sub in cat.get("subcategories", []) or []:
				sub_model = PersonaSubcategoryModel(
					id=str(uuid4()),
					category_id=cat_id,
					name=sub["name"],
					weight_percentage=int(sub["weight_percentage"]),
					level=sub.get("level"),
				)
				self.repo.add_subcategory(db, sub_model)

		event_bus.publish_event(PersonaCreatedEvent(id=created.id, job_description_id=created.job_description_id, name=created.name))
		return created
