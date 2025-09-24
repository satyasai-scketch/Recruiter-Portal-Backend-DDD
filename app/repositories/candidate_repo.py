from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy.orm import Session

from app.db.models.candidate import CandidateModel


class CandidateRepository:
	"""Repository interface for Candidate aggregates."""

	def get(self, db: Session, candidate_id: str) -> Optional[CandidateModel]:
		raise NotImplementedError

	def create(self, db: Session, candidate: CandidateModel) -> CandidateModel:
		raise NotImplementedError

	def update(self, db: Session, candidate: CandidateModel) -> CandidateModel:
		raise NotImplementedError

	def list_all(self, db: Session) -> Sequence[CandidateModel]:
		raise NotImplementedError


class SQLAlchemyCandidateRepository(CandidateRepository):
	"""SQLAlchemy-backed implementation of CandidateRepository."""

	def get(self, db: Session, candidate_id: str) -> Optional[CandidateModel]:
		return db.get(CandidateModel, candidate_id)

	def create(self, db: Session, candidate: CandidateModel) -> CandidateModel:
		db.add(candidate)
		db.commit()
		db.refresh(candidate)
		return candidate

	def update(self, db: Session, candidate: CandidateModel) -> CandidateModel:
		db.add(candidate)
		db.commit()
		db.refresh(candidate)
		return candidate

	def list_all(self, db: Session) -> Sequence[CandidateModel]:
		return db.query(CandidateModel).order_by(CandidateModel.name.asc()).all()
