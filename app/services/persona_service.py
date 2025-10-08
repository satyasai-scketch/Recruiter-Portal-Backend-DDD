from __future__ import annotations

from typing import Optional, Dict, List, Any
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
from app.services.persona_change_tracker import PersonaChangeTracker


class PersonaService:
	"""Orchestrates persona workflows at the application layer."""

	def __init__(self, repo: Optional[SQLAlchemyPersonaRepository] = None, level_repo: Optional[SQLAlchemyPersonaLevelRepository] = None, jd_repo: Optional[SQLAlchemyJobDescriptionRepository] = None):
		self.repo = repo or SQLAlchemyPersonaRepository()
		self.level_repo = level_repo or SQLAlchemyPersonaLevelRepository()
		self.jd_repo = jd_repo or SQLAlchemyJobDescriptionRepository()
	
	def get_persona(self, db: Session, persona_id: str) -> PersonaModel:
		return self.repo.get(db, persona_id)
	
	def list_by_jd(self, db: Session, job_description_id: str) -> List[PersonaModel]:
		return self.repo.list_by_jd(db, job_description_id)
	
	def list_all(self, db: Session) -> List[PersonaModel]:
		return self.repo.list_all(db)
	
	def count(self, db: Session) -> int:
		return self.repo.count(db)
	
	def get_change_logs(self, db: Session, persona_id: str) -> List[PersonaChangeLogModel]:
		"""Get all change logs for a persona, ordered by most recent first."""
		return self.repo.get_change_logs(db, persona_id)

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
				skillset_data = sub.get("skillset")
				if skillset_data:
					sub_skillset_id = str(uuid4())
					sub_skillset_model = PersonaSkillsetModel(
						id=sub_skillset_id,
						persona_id=created.id,
						persona_category_id=cat_id,
						persona_subcategory_id=sub_id,
						technologies=skillset_data.get("technologies", [])
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

	def update_persona(self, db: Session, persona_id: str, data: dict, updated_by: str) -> PersonaModel:
		"""Update a persona with comprehensive change tracking."""
		# Get the current persona with all relationships
		old_persona = self.repo.get(db, persona_id)
		if not old_persona:
			raise ValueError(f"Persona with ID '{persona_id}' not found")
		
		# Initialize change tracker
		change_tracker = PersonaChangeTracker()
		
		# Track changes before applying them
		change_logs = change_tracker.track_persona_changes(
			db, persona_id, old_persona, data, updated_by
		)
		
		# Apply updates to persona fields
		if 'name' in data:
			old_persona.name = data['name']
		if 'role_name' in data:
			old_persona.role_name = data['role_name']
		
		# Update categories if provided (includes notes and subcategories with skillsets)
		if 'categories' in data:
			self._update_categories(db, old_persona, data['categories'], updated_by)
		
		# Save the updated persona
		updated_persona = self.repo.update(db, old_persona)
		
		# Save all change logs
		for change_log in change_logs:
			self.repo.add_change_log(db, change_log)
		
		return updated_persona

	def _update_categories(self, db: Session, persona: PersonaModel, new_categories: list, updated_by: str) -> None:
		"""Update categories for a persona."""
		# Get existing categories
		existing_categories = {cat.id: cat for cat in persona.categories}
		new_category_ids = {cat.get('id') for cat in new_categories if cat.get('id')}
		
		# Delete categories that are no longer in the new data
		for cat_id, category in existing_categories.items():
			if cat_id not in new_category_ids:
				# Delete subcategories first (cascade should handle this, but being explicit)
				for subcat in category.subcategories:
					db.delete(subcat)
				db.delete(category)
		
		# Update or create categories
		for cat_data in new_categories:
			cat_id = cat_data.get('id')
			
			if cat_id and cat_id in existing_categories:
				# Update existing category
				category = existing_categories[cat_id]
				category.name = cat_data['name']
				category.weight_percentage = int(cat_data['weight_percentage'])
				category.range_min = cat_data.get('range_min')
				category.range_max = cat_data.get('range_max')
				category.position = cat_data.get('position')
				
				# Update category notes
				if 'notes' in cat_data:
					self._update_category_notes(db, category, cat_data['notes'], updated_by)
				
				# Update subcategories
				if 'subcategories' in cat_data:
					self._update_subcategories(db, category, cat_data['subcategories'], updated_by)
			else:
				# Create new category
				new_cat_id = cat_id or str(uuid4())
				category = PersonaCategoryModel(
					id=new_cat_id,
					persona_id=persona.id,
					name=cat_data['name'],
					weight_percentage=int(cat_data['weight_percentage']),
					range_min=cat_data.get('range_min'),
					range_max=cat_data.get('range_max'),
					position=cat_data.get('position')
				)
				db.add(category)
				
				# Create category notes
				if 'notes' in cat_data:
					self._create_category_notes(db, category, cat_data['notes'], updated_by)
				
				# Create subcategories
				if 'subcategories' in cat_data:
					self._create_subcategories(db, category, cat_data['subcategories'], updated_by)

	def _update_category_notes(self, db: Session, category: PersonaCategoryModel, new_notes: Any, updated_by: str) -> None:
		"""Update notes for a category."""
		# Get existing note for this category (single note, not a list)
		existing_note = category.notes if category.notes else None
		
		# Handle the note data (can be a single note object or a list)
		if new_notes:
			# If it's a list, take the first note; if it's a dict, use it directly
			if isinstance(new_notes, list):
				note_data = new_notes[0] if new_notes else None
			else:
				note_data = new_notes
			
			if note_data:
				note_id = note_data.get('id')
				
				if note_id and existing_note and note_id == existing_note.id:
					# Update existing note
					existing_note.custom_notes = note_data.get('custom_notes')
				else:
					# Delete existing note if it exists
					if existing_note:
						db.delete(existing_note)
						category.notes_id = None  # Clear the notes_id reference
					
					# Create new note
					new_note_id = note_id or str(uuid4())
					note = PersonaNotesModel(
						id=new_note_id,
						persona_id=category.persona_id,
						category_id=category.id,
						custom_notes=note_data.get('custom_notes')
					)
					db.add(note)
					category.notes_id = new_note_id  # Set the notes_id reference
		else:
			# No new notes - delete existing note if it exists
			if existing_note:
				db.delete(existing_note)
				category.notes_id = None  # Clear the notes_id reference

	def _create_category_notes(self, db: Session, category: PersonaCategoryModel, notes: Any, updated_by: str) -> None:
		"""Create new notes for a category."""
		# Handle the note data (can be a single note object or a list)
		if notes:
			# If it's a list, take the first note; if it's a dict, use it directly
			if isinstance(notes, list):
				note_data = notes[0] if notes else None
			else:
				note_data = notes
			
			if note_data:
				note_id = str(uuid4())
				note = PersonaNotesModel(
					id=note_id,
					persona_id=category.persona_id,
					category_id=category.id,
					custom_notes=note_data.get('custom_notes')
				)
				db.add(note)
				category.notes_id = note_id  # Set the notes_id reference

	def _update_subcategories(self, db: Session, category: PersonaCategoryModel, new_subcategories: list, updated_by: str) -> None:
		"""Update subcategories for a category."""
		existing_subcats = {sub.id: sub for sub in category.subcategories}
		new_subcat_ids = {sub.get('id') for sub in new_subcategories if sub.get('id')}
		
		# Delete subcategories that are no longer in the new data
		for sub_id, subcat in existing_subcats.items():
			if sub_id not in new_subcat_ids:
				db.delete(subcat)
		
		# Update or create subcategories
		for sub_data in new_subcategories:
			sub_id = sub_data.get('id')
			
			if sub_id and sub_id in existing_subcats:
				# Update existing subcategory
				subcat = existing_subcats[sub_id]
				subcat.name = sub_data['name']
				subcat.weight_percentage = int(sub_data['weight_percentage'])
				subcat.range_min = sub_data.get('range_min')
				subcat.range_max = sub_data.get('range_max')
				subcat.level_id = sub_data.get('level_id')
				subcat.position = sub_data.get('position')
				
				# Update subcategory skillset
				if 'skillset' in sub_data:
					self._update_subcategory_skillset(db, subcat, sub_data['skillset'], updated_by)
			else:
				# Create new subcategory
				new_sub_id = sub_id or str(uuid4())
				subcat = PersonaSubcategoryModel(
					id=new_sub_id,
					category_id=category.id,
					name=sub_data['name'],
					weight_percentage=int(sub_data['weight_percentage']),
					range_min=sub_data.get('range_min'),
					range_max=sub_data.get('range_max'),
					level_id=sub_data.get('level_id'),
					position=sub_data.get('position')
				)
				db.add(subcat)
				
				# Create subcategory skillset
				if 'skillset' in sub_data:
					self._create_subcategory_skillset(db, subcat, sub_data['skillset'], updated_by, category.persona_id, category.id)

	def _update_subcategory_skillset(self, db: Session, subcategory: PersonaSubcategoryModel, skillset_data: Any, updated_by: str) -> None:
		"""Update skillset for a subcategory."""
		# Get existing skillset for this subcategory
		existing_skillset = None
		for skillset in subcategory.category.persona.skillsets:
			if skillset.persona_subcategory_id == subcategory.id:
				existing_skillset = skillset
				break
		
		if skillset_data:
			if existing_skillset:
				# Update existing skillset
				existing_skillset.technologies = skillset_data.get('technologies', [])
			else:
				# Create new skillset
				skillset_id = str(uuid4())
				skillset = PersonaSkillsetModel(
					id=skillset_id,
					persona_id=subcategory.category.persona_id,
					persona_category_id=subcategory.category_id,
					persona_subcategory_id=subcategory.id,
					technologies=skillset_data.get('technologies', [])
				)
				db.add(skillset)
				subcategory.skillset_id = skillset_id  # Set the skillset_id reference
		else:
			# No skillset data - delete existing skillset if it exists
			if existing_skillset:
				db.delete(existing_skillset)
				subcategory.skillset_id = None  # Clear the skillset_id reference

	def _create_subcategory_skillset(self, db: Session, subcategory: PersonaSubcategoryModel, skillset_data: Any, updated_by: str, persona_id: str = None, category_id: str = None) -> None:
		"""Create new skillset for a subcategory."""
		if skillset_data:
			skillset_id = str(uuid4())
			# Use provided parameters or fall back to relationship access
			persona_id = persona_id or subcategory.category.persona_id
			category_id = category_id or subcategory.category_id
			
			skillset = PersonaSkillsetModel(
				id=skillset_id,
				persona_id=persona_id,
				persona_category_id=category_id,
				persona_subcategory_id=subcategory.id,
				technologies=skillset_data.get('technologies', [])
			)
			db.add(skillset)
			subcategory.skillset_id = skillset_id  # Set the skillset_id reference

	def _create_subcategories(self, db: Session, category: PersonaCategoryModel, subcategories: list, updated_by: str) -> None:
		"""Create new subcategories for a category."""
		for sub_data in subcategories:
			sub_id = str(uuid4())
			subcat = PersonaSubcategoryModel(
				id=sub_id,
				category_id=category.id,
				name=sub_data['name'],
				weight_percentage=int(sub_data['weight_percentage']),
				range_min=sub_data.get('range_min'),
				range_max=sub_data.get('range_max'),
				level_id=sub_data.get('level_id'),
				position=sub_data.get('position')
			)
			db.add(subcat)
			
			# Create subcategory skillset
			if 'skillset' in sub_data:
				self._create_subcategory_skillset(db, subcat, sub_data['skillset'], updated_by, category.persona_id, category.id)
