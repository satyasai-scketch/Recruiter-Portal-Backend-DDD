"""
Repository for CandidateCV operations.
"""

from __future__ import annotations

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.candidate import CandidateCVModel


class CandidateCVRepository:
	"""Repository interface for CandidateCV aggregates."""

	def get(self, db: Session, cv_id: str) -> Optional[CandidateCVModel]:
		raise NotImplementedError

	def create(self, db: Session, cv: CandidateCVModel) -> CandidateCVModel:
		raise NotImplementedError

	def update(self, db: Session, cv: CandidateCVModel) -> CandidateCVModel:
		raise NotImplementedError

	def find_by_hash(self, db: Session, file_hash: str) -> Optional[CandidateCVModel]:
		raise NotImplementedError

	def get_candidate_cvs(self, db: Session, candidate_id: str) -> List[CandidateCVModel]:
		raise NotImplementedError

	def get_next_version(self, db: Session, candidate_id: str) -> int:
		raise NotImplementedError

	def delete(self, db: Session, cv_id: str) -> bool:
		raise NotImplementedError


class SQLAlchemyCandidateCVRepository(CandidateCVRepository):
	"""SQLAlchemy-backed implementation of CandidateCVRepository."""

	def get(self, db: Session, cv_id: str) -> Optional[CandidateCVModel]:
		return db.get(CandidateCVModel, cv_id)

	def create(self, db: Session, cv: CandidateCVModel) -> CandidateCVModel:
		db.add(cv)
		db.commit()
		db.refresh(cv)
		return cv

	def update(self, db: Session, cv: CandidateCVModel) -> CandidateCVModel:
		db.add(cv)
		db.commit()
		db.refresh(cv)
		return cv

	def find_by_hash(self, db: Session, file_hash: str) -> Optional[CandidateCVModel]:
		return db.query(CandidateCVModel).filter(CandidateCVModel.file_hash == file_hash).first()

	def get_candidate_cvs(self, db: Session, candidate_id: str) -> List[CandidateCVModel]:
		return db.query(CandidateCVModel).filter(
			CandidateCVModel.candidate_id == candidate_id
		).order_by(CandidateCVModel.version.desc()).all()

	def get_next_version(self, db: Session, candidate_id: str) -> int:
		latest_cv = db.query(CandidateCVModel).filter(
			CandidateCVModel.candidate_id == candidate_id
		).order_by(CandidateCVModel.version.desc()).first()
		
		return (latest_cv.version + 1) if latest_cv else 1

	def delete(self, db: Session, cv_id: str) -> bool:
		"""Delete a candidate CV by ID."""
		try:
			cv = self.get(db, cv_id)
			if cv:
				db.delete(cv)
				db.commit()
				return True
			return False
		except Exception as e:
			db.rollback()
			raise e
