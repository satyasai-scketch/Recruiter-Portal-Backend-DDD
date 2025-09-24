from __future__ import annotations

from typing import Optional, Sequence, List
from sqlalchemy.orm import Session, selectinload

from app.db.models.persona import PersonaModel, PersonaCategoryModel, PersonaSubcategoryModel


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

	def delete_persona(self, db: Session, persona_id: str) -> None:
		raise NotImplementedError


class SQLAlchemyPersonaRepository(PersonaRepository):
	"""SQLAlchemy-backed implementation of PersonaRepository."""

	def get(self, db: Session, persona_id: str) -> Optional[PersonaModel]:
		return (
			db.query(PersonaModel)
			.options(selectinload(PersonaModel.categories).selectinload(PersonaCategoryModel.subcategories))
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
			.options(selectinload(PersonaModel.categories).selectinload(PersonaCategoryModel.subcategories))
			.filter(PersonaModel.job_description_id == jd_id)
			.order_by(PersonaModel.name.asc())
			.all()
		)

	def get_by_job_description(self, db: Session, jd_id: str) -> Sequence[PersonaModel]:
		return self.list_by_jd(db, jd_id)

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

	def delete_persona(self, db: Session, persona_id: str) -> None:
		obj = db.query(PersonaModel).filter(PersonaModel.id == persona_id).first()
		if obj:
			db.delete(obj)
			db.commit()
