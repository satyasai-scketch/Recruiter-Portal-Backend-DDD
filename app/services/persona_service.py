from __future__ import annotations

from typing import Optional, Dict
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.persona import (
	PersonaModel, PersonaCategoryModel, PersonaSubcategoryModel,
	PersonaSkillsetModel, PersonaNotesModel, PersonaChangeLogModel
)
from app.repositories.persona_repo import SQLAlchemyPersonaRepository
from app.repositories.persona_level_repo import SQLAlchemyPersonaLevelRepository
from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
from app.domain.persona import services as persona_domain_services
from app.domain.persona.entities import WeightInterval
from app.events.event_bus import event_bus
from app.events.persona_events import PersonaCreatedEvent


class PersonaService:
	"""Orchestrates persona workflows at the application layer."""

	def __init__(self, repo: Optional[SQLAlchemyPersonaRepository] = None, level_repo: Optional[SQLAlchemyPersonaLevelRepository] = None, jd_repo: Optional[SQLAlchemyJobDescriptionRepository] = None):
		self.repo = repo or SQLAlchemyPersonaRepository()
		self.level_repo = level_repo or SQLAlchemyPersonaLevelRepository()
		self.jd_repo = jd_repo or SQLAlchemyJobDescriptionRepository()

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

	def create_nested(self, db: Session, data: dict, created_by: str) -> PersonaModel:
		"""Create a nested persona graph with all related entities."""
		self._validate_nested_weights(data)
		persona_id = str(uuid4())
		
		# Get job description to extract role_name
		job_description = self.jd_repo.get(db, data["job_description_id"])
		if not job_description:
			raise ValueError(f"Job description with ID '{data['job_description_id']}' not found")
		
		role_name = job_description.job_role.name if job_description.job_role else None
		
		# Create main persona
		persona = PersonaModel(
			id=persona_id,
			job_description_id=data["job_description_id"],
			name=data["name"],
			role_name=role_name,
			created_by=created_by,
			weights=None,  # deprecated
			intervals=None,  # deprecated
		)
		created = self.repo.create(db, persona)

		# Create persona-level notes
		persona_notes = []
		for note_data in data.get("notes", []):
			note_id = str(uuid4())
			note_model = PersonaNotesModel(
				id=note_id,
				persona_id=created.id,
				custom_notes=note_data.get("custom_notes")
			)
			persona_notes.append(self.repo.add_note(db, note_model))

		# Create persona-level skillsets
		persona_skillsets = []
		for skillset_data in data.get("skillsets", []):
			skillset_id = str(uuid4())
			skillset_model = PersonaSkillsetModel(
				id=skillset_id,
				persona_id=created.id,
				technologies=skillset_data.get("technologies", [])
			)
			persona_skillsets.append(self.repo.add_skillset(db, skillset_model))

		# Create categories and their nested entities
		for cat in data.get("categories", []):
			cat_id = str(uuid4())
			
			# Create category notes if provided
			cat_notes_id = None
			if cat.get("notes"):
				cat_notes_id = str(uuid4())
				cat_note_model = PersonaNotesModel(
					id=cat_notes_id,
					persona_id=created.id,
					category_id=cat_id,
					custom_notes=cat["notes"].get("custom_notes")
				)
				self.repo.add_note(db, cat_note_model)
			
			cat_model = PersonaCategoryModel(
				id=cat_id,
				persona_id=created.id,
				name=cat["name"],
				weight_percentage=int(cat["weight_percentage"]),
				range_min=cat.get("range_min"),
				range_max=cat.get("range_max"),
				position=cat.get("position"),
				notes_id=cat_notes_id
			)
			created_category = self.repo.add_category(db, cat_model)

			# Create category-level skillsets
			for skillset_data in cat.get("skillsets", []):
				cat_skillset_id = str(uuid4())
				cat_skillset_model = PersonaSkillsetModel(
					id=cat_skillset_id,
					persona_id=created.id,
					persona_category_id=cat_id,
					technologies=skillset_data.get("technologies", [])
				)
				self.repo.add_skillset(db, cat_skillset_model)

			# Create subcategories
			for sub in cat.get("subcategories", []):
				sub_id = str(uuid4())
				
				# Handle level_id - if it's a string like "lvl-003", try to find the level
				level_id = sub.get("level_id")

				level = self.level_repo.get_by_position(db, level_id)
				if level:
					level_id = level.id
				
				# Create subcategory skillset if provided
				sub_skillset_id = None
				if sub.get("skillset"):
					sub_skillset_id = str(uuid4())
					sub_skillset_model = PersonaSkillsetModel(
						id=sub_skillset_id,
						persona_id=created.id,
						persona_category_id=cat_id,
						persona_subcategory_id=sub_id,
						technologies=sub["skillset"].get("technologies", [])
					)
					self.repo.add_skillset(db, sub_skillset_model)
				
				sub_model = PersonaSubcategoryModel(
					id=sub_id,
					category_id=cat_id,
					name=sub["name"],
					weight_percentage=int(sub["weight_percentage"]),
					range_min=sub.get("range_min"),
					range_max=sub.get("range_max"),
					level_id=level_id,
					skillset_id=sub_skillset_id,
					position=sub.get("position")
				)
				self.repo.add_subcategory(db, sub_model)

		# Create change logs
		for change_log_data in data.get("change_logs", []):
			change_log_id = str(uuid4())
			change_log_model = PersonaChangeLogModel(
				id=change_log_id,
				persona_id=created.id,
				entity_type=change_log_data["entity_type"],
				entity_id=change_log_data["entity_id"],
				field_name=change_log_data["field_name"],
				old_value=change_log_data.get("old_value"),
				new_value=change_log_data.get("new_value"),
				changed_by=created_by  # Use the current user instead of payload
			)
			self.repo.add_change_log(db, change_log_model)

		event_bus.publish_event(PersonaCreatedEvent(id=created.id, job_description_id=created.job_description_id, name=created.name))
		return created
