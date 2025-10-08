from __future__ import annotations

from typing import Optional, Sequence, List
from sqlalchemy.orm import Session, selectinload

from app.db.models.persona import (
	PersonaModel, PersonaCategoryModel, PersonaSubcategoryModel,
	PersonaSkillsetModel, PersonaNotesModel, PersonaChangeLogModel
)


class PersonaRepository:
	"""Repository interface for Persona aggregates."""

	def get(self, db: Session, persona_id: str) -> Optional[PersonaModel]:
		raise NotImplementedError

	def create(self, db: Session, persona: PersonaModel) -> PersonaModel:
		raise NotImplementedError

	def update(self, db: Session, persona: PersonaModel) -> PersonaModel:
		raise NotImplementedError

	def list_by_jd(self, db: Session, jd_id: str) -> Sequence[PersonaModel]:
		raise NotImplementedError

	def get_by_job_description(self, db: Session, jd_id: str) -> Sequence[PersonaModel]:
		raise NotImplementedError

	# Category-level CRUD
	def add_category(self, db: Session, category: PersonaCategoryModel) -> PersonaCategoryModel:
		raise NotImplementedError

	def add_subcategory(self, db: Session, subcat: PersonaSubcategoryModel) -> PersonaSubcategoryModel:
		raise NotImplementedError

	def add_skillset(self, db: Session, skillset: PersonaSkillsetModel) -> PersonaSkillsetModel:
		raise NotImplementedError

	def add_note(self, db: Session, note: PersonaNotesModel) -> PersonaNotesModel:
		raise NotImplementedError

	def add_change_log(self, db: Session, change_log: PersonaChangeLogModel) -> PersonaChangeLogModel:
		raise NotImplementedError

	def get_change_logs(self, db: Session, persona_id: str) -> List[PersonaChangeLogModel]:
		raise NotImplementedError

	def delete_persona(self, db: Session, persona_id: str) -> None:
		raise NotImplementedError


class SQLAlchemyPersonaRepository(PersonaRepository):
	"""SQLAlchemy-backed implementation of PersonaRepository."""

	def get(self, db: Session, persona_id: str) -> Optional[PersonaModel]:
		return (
			db.query(PersonaModel)
			.options(
				selectinload(PersonaModel.categories).selectinload(PersonaCategoryModel.subcategories),
				selectinload(PersonaModel.skillsets),
				selectinload(PersonaModel.notes),
				selectinload(PersonaModel.change_logs)
			)
			.filter(PersonaModel.id == persona_id)
			.first()
		)

	def create(self, db: Session, persona: PersonaModel) -> PersonaModel:
		db.add(persona)
		db.commit()
		db.refresh(persona)
		return persona

	def update(self, db: Session, persona: PersonaModel) -> PersonaModel:
		db.add(persona)
		db.commit()
		db.refresh(persona)
		return persona

	def list_by_jd(self, db: Session, jd_id: str) -> Sequence[PersonaModel]:
		return (
			db.query(PersonaModel)
			.options(
				selectinload(PersonaModel.categories).selectinload(PersonaCategoryModel.subcategories),
				selectinload(PersonaModel.skillsets),
				selectinload(PersonaModel.notes),
				selectinload(PersonaModel.change_logs)
			)
			.filter(PersonaModel.job_description_id == jd_id)
			.order_by(PersonaModel.name.asc())
			.all()
		)

	def get_by_job_description(self, db: Session, jd_id: str) -> Sequence[PersonaModel]:
		return self.list_by_jd(db, jd_id)

	def list_all(self, db: Session) -> Sequence[PersonaModel]:
		return db.query(PersonaModel).all()
	
	def count(self, db: Session) -> int:
		return db.query(PersonaModel).count()

	def add_category(self, db: Session, category: PersonaCategoryModel) -> PersonaCategoryModel:
		db.add(category)
		db.commit()
		db.refresh(category)
		return category

	def add_subcategory(self, db: Session, subcat: PersonaSubcategoryModel) -> PersonaSubcategoryModel:
		db.add(subcat)
		db.commit()
		db.refresh(subcat)
		return subcat

	def add_skillset(self, db: Session, skillset: PersonaSkillsetModel) -> PersonaSkillsetModel:
		db.add(skillset)
		db.commit()
		db.refresh(skillset)
		return skillset

	def add_note(self, db: Session, note: PersonaNotesModel) -> PersonaNotesModel:
		db.add(note)
		db.commit()
		db.refresh(note)
		return note

	def add_change_log(self, db: Session, change_log: PersonaChangeLogModel) -> PersonaChangeLogModel:
		db.add(change_log)
		db.commit()
		db.refresh(change_log)
		return change_log

	def get_change_logs(self, db: Session, persona_id: str) -> List[PersonaChangeLogModel]:
		"""Get all change logs for a persona, ordered by most recent first."""
		return (
			db.query(PersonaChangeLogModel)
			.options(selectinload(PersonaChangeLogModel.user))
			.filter(PersonaChangeLogModel.persona_id == persona_id)
			.order_by(PersonaChangeLogModel.changed_at.desc())
			.all()
		)

	def delete_persona(self, db: Session, persona_id: str) -> None:
		obj = db.query(PersonaModel).filter(PersonaModel.id == persona_id).first()
		if obj:
			db.delete(obj)
			db.commit()
