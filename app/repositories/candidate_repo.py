from __future__ import annotations

from typing import Optional, Sequence, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.candidate import CandidateModel, CandidateCVModel


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

	def find_by_email(self, db: Session, email: str) -> Optional[CandidateModel]:
		raise NotImplementedError

	def find_by_phone(self, db: Session, phone: str) -> Optional[CandidateModel]:
		raise NotImplementedError

	def find_by_email_or_phone(self, db: Session, email: Optional[str], phone: Optional[str]) -> Optional[CandidateModel]:
		raise NotImplementedError

	def delete(self, db: Session, candidate_id: str) -> bool:
		raise NotImplementedError


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
		return db.query(CandidateModel).order_by(CandidateModel.full_name.asc()).all()

	def find_by_email(self, db: Session, email: str) -> Optional[CandidateModel]:
		return db.query(CandidateModel).filter(CandidateModel.email == email).first()

	def find_by_phone(self, db: Session, phone: str) -> Optional[CandidateModel]:
		return db.query(CandidateModel).filter(CandidateModel.phone == phone).first()

	def find_by_email_or_phone(self, db: Session, email: Optional[str], phone: Optional[str]) -> Optional[CandidateModel]:
		query = db.query(CandidateModel)
		conditions = []
		
		if email:
			conditions.append(CandidateModel.email == email)
		if phone:
			conditions.append(CandidateModel.phone == phone)
		
		if not conditions:
			return None
		
		return query.filter(and_(*conditions)).first()

	def delete(self, db: Session, candidate_id: str) -> bool:
		"""Delete a candidate by ID."""
		try:
			candidate = self.get(db, candidate_id)
			if candidate:
				db.delete(candidate)
				db.commit()
				return True
			return False
		except Exception as e:
			db.rollback()
			raise e


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
