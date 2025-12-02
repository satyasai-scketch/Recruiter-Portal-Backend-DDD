# app/repositories/candidate_selection_status_repo.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.candidate_selection_status import CandidateSelectionStatusModel


class CandidateSelectionStatusRepository:
	"""Repository for Candidate Selection Status data access operations."""
	
	def create(self, db: Session, status_data: dict) -> CandidateSelectionStatusModel:
		"""Create a new candidate selection status."""
		try:
			# Convert is_active boolean to string for SQLite compatibility
			if 'is_active' in status_data and isinstance(status_data['is_active'], bool):
				status_data['is_active'] = "true" if status_data['is_active'] else "false"
			
			status = CandidateSelectionStatusModel(**status_data)
			db.add(status)
			db.commit()
			db.refresh(status)
			return status
		except Exception as e:
			db.rollback()
			raise e
	
	def get_by_id(self, db: Session, status_id: str) -> Optional[CandidateSelectionStatusModel]:
		"""Get status by ID."""
		return db.query(CandidateSelectionStatusModel).filter(
			CandidateSelectionStatusModel.id == status_id
		).first()
	
	def get_by_code(self, db: Session, code: str) -> Optional[CandidateSelectionStatusModel]:
		"""Get status by code."""
		return db.query(CandidateSelectionStatusModel).filter(
			CandidateSelectionStatusModel.code == code
		).first()
	
	def get_all(self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[CandidateSelectionStatusModel]:
		"""Get all statuses with pagination."""
		query = db.query(CandidateSelectionStatusModel)
		
		if active_only:
			query = query.filter(CandidateSelectionStatusModel.is_active == "true")
		
		return query.order_by(
			CandidateSelectionStatusModel.display_order.asc(),
			CandidateSelectionStatusModel.name.asc()
		).offset(skip).limit(limit).all()
	
	def get_active(self, db: Session) -> List[CandidateSelectionStatusModel]:
		"""Get all active statuses ordered by display_order."""
		return db.query(CandidateSelectionStatusModel).filter(
			CandidateSelectionStatusModel.is_active == "true"
		).order_by(
			CandidateSelectionStatusModel.display_order.asc(),
			CandidateSelectionStatusModel.name.asc()
		).all()
	
	def update(self, db: Session, status: CandidateSelectionStatusModel) -> CandidateSelectionStatusModel:
		"""Update an existing status."""
		try:
			db.add(status)
			db.commit()
			db.refresh(status)
			return status
		except Exception as e:
			db.rollback()
			raise e
	
	def delete(self, db: Session, status_id: str) -> bool:
		"""Delete a status."""
		try:
			status = self.get_by_id(db, status_id)
			if not status:
				return False
			
			db.delete(status)
			db.commit()
			return True
		except Exception as e:
			db.rollback()
			raise e
	
	def count(self, db: Session, active_only: bool = False) -> int:
		"""Count total number of statuses."""
		query = db.query(CandidateSelectionStatusModel)
		
		if active_only:
			query = query.filter(CandidateSelectionStatusModel.is_active == "true")
		
		return query.count()

