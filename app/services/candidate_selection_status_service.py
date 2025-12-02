# app/services/candidate_selection_status_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from app.repositories.candidate_selection_status_repo import CandidateSelectionStatusRepository
from app.db.models.candidate_selection_status import CandidateSelectionStatusModel


class CandidateSelectionStatusService:
	"""Application service for Candidate Selection Status operations."""
	
	def __init__(self):
		self.repo = CandidateSelectionStatusRepository()
	
	def create(self, db: Session, data: dict) -> CandidateSelectionStatusModel:
		"""Create a new candidate selection status."""
		try:
			# Check if code already exists
			existing = self.repo.get_by_code(db, data.get("code"))
			if existing:
				raise ValueError(f"Status with code '{data.get('code')}' already exists")
			
			# Prepare model data
			model_data = {
				"id": str(uuid4()),
				"code": data.get("code"),
				"name": data.get("name"),
				"description": data.get("description"),
				"display_order": data.get("display_order", 0),
				"is_active": data.get("is_active", True),
				"created_by": data.get("created_by"),
				"updated_by": data.get("created_by"),  # Set updated_by same as created_by on creation
			}
			
			return self.repo.create(db, model_data)
			
		except Exception as e:
			db.rollback()
			raise e
	
	def get_by_id(self, db: Session, status_id: str) -> Optional[CandidateSelectionStatusModel]:
		"""Get status by ID."""
		return self.repo.get_by_id(db, status_id)
	
	def get_by_code(self, db: Session, code: str) -> Optional[CandidateSelectionStatusModel]:
		"""Get status by code."""
		return self.repo.get_by_code(db, code)
	
	def list_all(self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[CandidateSelectionStatusModel]:
		"""List all statuses with pagination."""
		return self.repo.get_all(db, skip, limit, active_only)
	
	def list_active(self, db: Session) -> List[CandidateSelectionStatusModel]:
		"""List all active statuses."""
		return self.repo.get_active(db)
	
	def update(self, db: Session, status_id: str, data: dict) -> Optional[CandidateSelectionStatusModel]:
		"""Update an existing status."""
		try:
			status = self.repo.get_by_id(db, status_id)
			if not status:
				return None
			
			# Check if code is being changed and if new code already exists
			if "code" in data and data["code"] != status.code:
				existing = self.repo.get_by_code(db, data["code"])
				if existing:
					raise ValueError(f"Status with code '{data['code']}' already exists")
			
			# Update fields
			if "code" in data:
				status.code = data["code"]
			if "name" in data:
				status.name = data["name"]
			if "description" in data:
				status.description = data["description"]
			if "display_order" in data:
				status.display_order = data["display_order"]
			if "is_active" in data:
				status.is_active = "true" if data["is_active"] else "false"
			if "updated_by" in data:
				status.updated_by = data["updated_by"]
			
			status.updated_at = datetime.now()
			
			return self.repo.update(db, status)
			
		except Exception as e:
			db.rollback()
			raise e
	
	def delete(self, db: Session, status_id: str) -> bool:
		"""Delete a status."""
		try:
			# Check if status is being used in any selections
			from app.db.models.candidate import CandidateSelectionModel
			selections_count = db.query(CandidateSelectionModel).filter(
				CandidateSelectionModel.status == status_id
			).count()
			
			if selections_count > 0:
				raise ValueError(f"Cannot delete status: it is being used by {selections_count} candidate selection(s)")
			
			return self.repo.delete(db, status_id)
			
		except Exception as e:
			db.rollback()
			raise e
	
	def count(self, db: Session, active_only: bool = False) -> int:
		"""Count total number of statuses."""
		return self.repo.count(db, active_only)

