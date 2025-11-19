from __future__ import annotations

from typing import Optional, Sequence, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, distinct

from app.db.models.candidate import CandidateModel, CandidateCVModel, CandidateSelectionModel, CandidateSelectionAuditLogModel
from app.db.models.score import CandidateScoreModel
from app.db.models.persona import PersonaModel


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
		return (
			db.query(CandidateModel)
			.options(
				# Load creator for created_by_name
				joinedload(CandidateModel.creator),
				# Load updater for updated_by_name
				joinedload(CandidateModel.updater)
			)
			.filter(CandidateModel.id == candidate_id)
			.first()
		)

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

	def list_all(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[CandidateModel]:
		"""List all candidates with eagerly loaded relationships for list view."""
		return (
			db.query(CandidateModel)
			.options(
				# Load creator for created_by_name
				joinedload(CandidateModel.creator),
				# Load updater for updated_by_name
				joinedload(CandidateModel.updater)
			)
			.order_by(CandidateModel.created_at.desc())
			.offset(skip)
			.limit(limit)
			.all()
		)
	
	def count(self, db: Session) -> int:
		"""Count total candidates."""
		return db.query(CandidateModel).count()
	
	def get_personas_for_candidate(self, db: Session, candidate_id: str) -> List[dict]:
		"""Get distinct personas evaluated against a candidate."""
		results = (
			db.query(
				PersonaModel.id.label('persona_id'),
				PersonaModel.name.label('persona_name')
			)
			.join(CandidateScoreModel, PersonaModel.id == CandidateScoreModel.persona_id)
			.filter(CandidateScoreModel.candidate_id == candidate_id)
			.distinct()
			.all()
		)
		return [{"persona_id": r.persona_id, "persona_name": r.persona_name} for r in results]

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


class CandidateSelectionRepository:
	"""Repository interface for Candidate Selection aggregates."""

	def create(self, db: Session, selection: CandidateSelectionModel) -> CandidateSelectionModel:
		raise NotImplementedError

	def get(self, db: Session, selection_id: str) -> Optional[CandidateSelectionModel]:
		raise NotImplementedError

	def get_by_candidate_persona(self, db: Session, candidate_id: str, persona_id: str) -> Optional[CandidateSelectionModel]:
		raise NotImplementedError

	def list_selections(
		self, 
		db: Session, 
		persona_id: Optional[str] = None,
		job_description_id: Optional[str] = None,
		status: Optional[str] = None,
		skip: int = 0,
		limit: int = 100
	) -> Tuple[Sequence[CandidateSelectionModel], int]:
		raise NotImplementedError

	def update(self, db: Session, selection: CandidateSelectionModel) -> CandidateSelectionModel:
		raise NotImplementedError

	def delete(self, db: Session, selection_id: str) -> bool:
		raise NotImplementedError

	def bulk_create(self, db: Session, selections: List[CandidateSelectionModel]) -> List[CandidateSelectionModel]:
		raise NotImplementedError


class SQLAlchemyCandidateSelectionRepository(CandidateSelectionRepository):
	"""SQLAlchemy-backed implementation of CandidateSelectionRepository."""

	def create(self, db: Session, selection: CandidateSelectionModel) -> CandidateSelectionModel:
		"""Create a new candidate selection."""
		db.add(selection)
		db.commit()
		db.refresh(selection)
		return selection

	def get(self, db: Session, selection_id: str) -> Optional[CandidateSelectionModel]:
		"""Get a candidate selection by ID with relationships loaded."""
		return (
			db.query(CandidateSelectionModel)
			.options(
				joinedload(CandidateSelectionModel.candidate),
				joinedload(CandidateSelectionModel.persona),
				joinedload(CandidateSelectionModel.job_description),
				joinedload(CandidateSelectionModel.selector)
			)
			.filter(CandidateSelectionModel.id == selection_id)
			.first()
		)

	def get_by_candidate_persona(self, db: Session, candidate_id: str, persona_id: str) -> Optional[CandidateSelectionModel]:
		"""Get a selection by candidate_id and persona_id."""
		return (
			db.query(CandidateSelectionModel)
			.options(
				joinedload(CandidateSelectionModel.candidate),
				joinedload(CandidateSelectionModel.persona),
				joinedload(CandidateSelectionModel.job_description),
				joinedload(CandidateSelectionModel.selector)
			)
			.filter(
				CandidateSelectionModel.candidate_id == candidate_id,
				CandidateSelectionModel.persona_id == persona_id
			)
			.first()
		)

	def list_selections(
		self, 
		db: Session, 
		persona_id: Optional[str] = None,
		job_description_id: Optional[str] = None,
		status: Optional[str] = None,
		skip: int = 0,
		limit: int = 100
	) -> Tuple[Sequence[CandidateSelectionModel], int]:
		"""List candidate selections with optional filtering and pagination.
		
		Returns:
			Tuple of (list of selections, total count)
		"""
		query = db.query(CandidateSelectionModel).options(
			joinedload(CandidateSelectionModel.candidate),
			joinedload(CandidateSelectionModel.persona),
			joinedload(CandidateSelectionModel.job_description),
			joinedload(CandidateSelectionModel.selector)
		)
		
		# Apply filters
		if persona_id:
			query = query.filter(CandidateSelectionModel.persona_id == persona_id)
		if job_description_id:
			query = query.filter(CandidateSelectionModel.job_description_id == job_description_id)
		if status:
			query = query.filter(CandidateSelectionModel.status == status)
		
		# Get total count before pagination
		total = query.count()
		
		# Apply pagination and ordering
		selections = (
			query
			.order_by(CandidateSelectionModel.created_at.desc())
			.offset(skip)
			.limit(limit)
			.all()
		)
		
		return selections, total

	def update(self, db: Session, selection: CandidateSelectionModel) -> CandidateSelectionModel:
		"""Update a candidate selection."""
		db.add(selection)
		db.commit()
		db.refresh(selection)
		return selection

	def delete(self, db: Session, selection_id: str) -> bool:
		"""Delete a candidate selection by ID."""
		try:
			selection = self.get(db, selection_id)
			if selection:
				db.delete(selection)
				db.commit()
				return True
			return False
		except Exception as e:
			db.rollback()
			raise e

	def bulk_create(self, db: Session, selections: List[CandidateSelectionModel]) -> List[CandidateSelectionModel]:
		"""Bulk create candidate selections."""
		try:
			db.add_all(selections)
			db.commit()
			for selection in selections:
				db.refresh(selection)
			return selections
		except Exception as e:
			db.rollback()
			raise e


class CandidateSelectionAuditLogRepository:
	"""Repository interface for Candidate Selection Audit Log aggregates."""

	def create(self, db: Session, audit_log: CandidateSelectionAuditLogModel) -> CandidateSelectionAuditLogModel:
		raise NotImplementedError

	def get_by_selection_id(
		self, 
		db: Session, 
		selection_id: str,
		skip: int = 0,
		limit: int = 100
	) -> Sequence[CandidateSelectionAuditLogModel]:
		raise NotImplementedError

	def count_by_selection_id(self, db: Session, selection_id: str) -> int:
		raise NotImplementedError


class SQLAlchemyCandidateSelectionAuditLogRepository(CandidateSelectionAuditLogRepository):
	"""SQLAlchemy-backed implementation of CandidateSelectionAuditLogRepository."""

	def create(self, db: Session, audit_log: CandidateSelectionAuditLogModel) -> CandidateSelectionAuditLogModel:
		"""Create a new audit log entry."""
		db.add(audit_log)
		db.commit()
		db.refresh(audit_log)
		return audit_log

	def get_by_selection_id(
		self, 
		db: Session, 
		selection_id: str,
		skip: int = 0,
		limit: int = 100
	) -> Sequence[CandidateSelectionAuditLogModel]:
		"""Get audit logs for a specific selection, ordered by creation time (oldest first)."""
		return (
			db.query(CandidateSelectionAuditLogModel)
			.options(
				joinedload(CandidateSelectionAuditLogModel.changer)
			)
			.filter(CandidateSelectionAuditLogModel.selection_id == selection_id)
			.order_by(CandidateSelectionAuditLogModel.created_at.asc())
			.offset(skip)
			.limit(limit)
			.all()
		)

	def count_by_selection_id(self, db: Session, selection_id: str) -> int:
		"""Count audit logs for a specific selection."""
		return (
			db.query(CandidateSelectionAuditLogModel)
			.filter(CandidateSelectionAuditLogModel.selection_id == selection_id)
			.count()
		)
