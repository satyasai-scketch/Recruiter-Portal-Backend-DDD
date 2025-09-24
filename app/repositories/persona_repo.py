from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy.orm import Session

from app.db.models.persona import PersonaModel


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


class SQLAlchemyPersonaRepository(PersonaRepository):
	"""SQLAlchemy-backed implementation of PersonaRepository."""

	def get(self, db: Session, persona_id: str) -> Optional[PersonaModel]:
		return db.get(PersonaModel, persona_id)

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
			.filter(PersonaModel.job_description_id == jd_id)
			.order_by(PersonaModel.name.asc())
			.all()
		)
