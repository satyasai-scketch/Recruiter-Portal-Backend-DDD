# app/api/v1/candidate_selection_status.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import db_session, get_current_user
from app.schemas.candidate_selection_status import (
	CandidateSelectionStatusCreate,
	CandidateSelectionStatusUpdate,
	CandidateSelectionStatusRead,
	CandidateSelectionStatusSimple,
	CandidateSelectionStatusListResponse,
	CandidateSelectionStatusResponse
)
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.candidate_selection_status_commands import (
	CreateCandidateSelectionStatus,
	UpdateCandidateSelectionStatus,
	DeleteCandidateSelectionStatus
)
from app.cqrs.queries.candidate_selection_status_queries import (
	GetCandidateSelectionStatus,
	GetCandidateSelectionStatusByCode,
	ListCandidateSelectionStatuses,
	ListActiveCandidateSelectionStatuses,
	CountCandidateSelectionStatuses
)
from app.utils.error_handlers import handle_service_errors, rollback_on_error
from app.db.models.user import UserModel

router = APIRouter()


@router.post("/", response_model=CandidateSelectionStatusRead, summary="Create Candidate Selection Status")
async def create_status(
	status_data: CandidateSelectionStatusCreate,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	Create a new candidate selection status.
	
	- **code**: Status code (e.g., 'selected', 'interview_scheduled') - must be unique
	- **name**: Display name (e.g., 'Selected', 'Interview Scheduled')
	- **description**: Optional description
	- **display_order**: Order for dropdown display (default: 0)
	- **is_active**: Whether the status is active (default: true)
	"""
	try:
		# Convert Pydantic model to dict and add user info
		payload = status_data.model_dump()
		payload["created_by"] = user.id
		
		# Create status using CQRS
		created_status = handle_command(db, CreateCandidateSelectionStatus(payload))
		
		return CandidateSelectionStatusRead.model_validate(created_status)
	
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.get("/{status_id}", response_model=CandidateSelectionStatusRead, summary="Get Status by ID")
async def get_status(
	status_id: str,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	Get candidate selection status information by ID.
	"""
	status = handle_query(db, GetCandidateSelectionStatus(status_id))
	
	if not status:
		raise HTTPException(status_code=404, detail="Status not found")
	
	return CandidateSelectionStatusRead.model_validate(status)


@router.get("/code/{code}", response_model=CandidateSelectionStatusRead, summary="Get Status by Code")
async def get_status_by_code(
	code: str,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	Get candidate selection status information by code.
	"""
	status = handle_query(db, GetCandidateSelectionStatusByCode(code))
	
	if not status:
		raise HTTPException(status_code=404, detail="Status not found")
	
	return CandidateSelectionStatusRead.model_validate(status)


@router.get("/", response_model=CandidateSelectionStatusListResponse, summary="List Statuses")
async def list_statuses(
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	active_only: bool = Query(False, description="Show only active statuses"),
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	List all candidate selection statuses with pagination.
	
	Statuses are ordered by display_order, then by name.
	"""
	skip = (page - 1) * size
	
	# Get statuses and total count
	statuses = handle_query(db, ListCandidateSelectionStatuses(skip, size, active_only))
	total = handle_query(db, CountCandidateSelectionStatuses(active_only))
	
	# Convert to response format
	status_reads = [CandidateSelectionStatusRead.model_validate(status) for status in statuses]
	
	return CandidateSelectionStatusListResponse(
		statuses=status_reads,
		total=total,
		page=page,
		size=size,
		has_next=(skip + size) < total,
		has_prev=page > 1
	)


@router.get("/simple/active", response_model=List[CandidateSelectionStatusSimple], summary="Get Active Statuses (Simple)")
async def get_active_statuses_simple(
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	Get all active candidate selection statuses in a simple format for dropdowns.
	
	This endpoint returns statuses ordered by display_order, then by name.
	Used by frontend to populate status dropdowns.
	"""
	statuses = handle_query(db, ListActiveCandidateSelectionStatuses())
	
	return [CandidateSelectionStatusSimple.model_validate(status) for status in statuses]


@router.put("/{status_id}", response_model=CandidateSelectionStatusRead, summary="Update Status")
async def update_status(
	status_id: str,
	status_data: CandidateSelectionStatusUpdate,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	Update candidate selection status information.
	
	All fields are optional. Only provided fields will be updated.
	"""
	try:
		# Convert Pydantic model to dict and add user info
		payload = status_data.model_dump(exclude_unset=True)
		payload["updated_by"] = user.id
		
		# Update status using CQRS
		updated_status = handle_command(db, UpdateCandidateSelectionStatus(status_id, payload))
		
		if not updated_status:
			raise HTTPException(status_code=404, detail="Status not found")
		
		return CandidateSelectionStatusRead.model_validate(updated_status)
	
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.delete("/{status_id}", response_model=CandidateSelectionStatusResponse, summary="Delete Status")
async def delete_status(
	status_id: str,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	Delete a candidate selection status.
	
	Status cannot be deleted if it is being used by any candidate selections.
	"""
	try:
		# Delete status using CQRS
		success = handle_command(db, DeleteCandidateSelectionStatus(status_id))
		
		if not success:
			raise HTTPException(status_code=404, detail="Status not found")
		
		return CandidateSelectionStatusResponse(
			message="Status deleted successfully"
		)
	
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)

