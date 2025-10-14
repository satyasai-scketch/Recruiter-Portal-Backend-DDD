from typing import List, Dict

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.schemas.candidate import (
	CandidateCreate, 
	CandidateRead, 
	CandidateUploadResponse,
	CandidateListResponse,
	CandidateCVRead,
	CandidateCVListResponse,
	CandidateDeleteResponse,
	CandidateCVDeleteResponse
)
from app.cqrs.handlers import UploadCVs, ScoreCandidates, handle_command, handle_query
from app.cqrs.commands.upload_cv_file import UploadCVFile
from app.cqrs.commands.candidate_commands import DeleteCandidate, DeleteCandidateCV
from app.cqrs.queries.candidate_queries import (
	GetCandidate,
	ListAllCandidates,
	GetCandidateCV,
	GetCandidateCVs
)

router = APIRouter()


def _convert_candidate_model_to_read_schema(candidate_model) -> CandidateRead:
	"""Convert CandidateModel to CandidateRead schema format."""
	return CandidateRead(
		id=candidate_model.id,
		full_name=candidate_model.full_name,
		email=candidate_model.email,
		phone=candidate_model.phone,
		latest_cv_id=candidate_model.latest_cv_id,
		created_at=candidate_model.created_at,
		updated_at=candidate_model.updated_at,
		cvs=None  # CVs are loaded separately when needed
	)


def _convert_cv_model_to_read_schema(cv_model) -> CandidateCVRead:
	"""Convert CandidateCVModel to CandidateCVRead schema format."""
	return CandidateCVRead(
		id=cv_model.id,
		candidate_id=cv_model.candidate_id,
		file_name=cv_model.file_name,
		file_hash=cv_model.file_hash,
		version=cv_model.version,
		s3_url=cv_model.s3_url,
		file_size=cv_model.file_size,
		mime_type=cv_model.mime_type,
		status=cv_model.status,
		uploaded_at=cv_model.uploaded_at,
		cv_text=cv_model.cv_text,
		skills=cv_model.skills,
		roles_detected=cv_model.roles_detected
	)


@router.get("/", response_model=CandidateListResponse, summary="List All Candidates")
async def list_candidates(
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	List all candidates with pagination.
	"""
	skip = (page - 1) * size
	
	# Get candidates
	candidates = handle_query(db, ListAllCandidates(skip, size))
	
	# Get total count (we'll need to add this to the service)
	# For now, we'll use the length of all candidates
	all_candidates = handle_query(db, ListAllCandidates(0, 10000))  # Get a large number to count
	total = len(all_candidates)
	
	# Convert to response format
	candidate_reads = [_convert_candidate_model_to_read_schema(candidate) for candidate in candidates]
	
	return CandidateListResponse(
		candidates=candidate_reads,
		total=total,
		page=page,
		size=size,
		has_next=(skip + size) < total,
		has_prev=page > 1
	)


@router.get("/{candidate_id}", response_model=CandidateRead, summary="Get Candidate by ID")
async def get_candidate(
	candidate_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get candidate information by ID.
	"""
	candidate = handle_query(db, GetCandidate(candidate_id))
	
	if not candidate:
		raise HTTPException(status_code=404, detail="Candidate not found")
	
	# Load CVs for this candidate
	cvs = handle_query(db, GetCandidateCVs(candidate_id))
	
	# Convert to response format with CVs included
	candidate_read = _convert_candidate_model_to_read_schema(candidate)
	candidate_read.cvs = [_convert_cv_model_to_read_schema(cv) for cv in cvs]
	
	return candidate_read


@router.get("/{candidate_id}/cvs", response_model=CandidateCVListResponse, summary="Get Candidate CVs")
async def get_candidate_cvs(
	candidate_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get all CVs for a specific candidate.
	"""
	# First check if candidate exists
	candidate = handle_query(db, GetCandidate(candidate_id))
	if not candidate:
		raise HTTPException(status_code=404, detail="Candidate not found")
	
	# Get candidate CVs
	cvs = handle_query(db, GetCandidateCVs(candidate_id))
	
	# Convert to response format
	cv_reads = [_convert_cv_model_to_read_schema(cv) for cv in cvs]
	
	return CandidateCVListResponse(
		cvs=cv_reads,
		candidate_id=candidate_id,
		total=len(cv_reads)
	)


@router.get("/cvs/{candidate_cv_id}", response_model=CandidateCVRead, summary="Get Candidate CV by ID")
async def get_candidate_cv(
	candidate_cv_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get candidate CV information by CV ID.
	"""
	cv = handle_query(db, GetCandidateCV(candidate_cv_id))
	
	if not cv:
		raise HTTPException(status_code=404, detail="Candidate CV not found")
	
	return _convert_cv_model_to_read_schema(cv)


@router.delete("/{candidate_id}", response_model=CandidateDeleteResponse, summary="Delete Candidate")
async def delete_candidate(
	candidate_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Delete a candidate and all associated CVs.
	
	This will permanently delete:
	- The candidate record
	- All associated CV files from storage
	- All CV records from the database
	
	This action cannot be undone.
	"""
	# First check if candidate exists
	candidate = handle_query(db, GetCandidate(candidate_id))
	if not candidate:
		raise HTTPException(status_code=404, detail="Candidate not found")
	
	# Delete candidate using CQRS
	success = handle_command(db, DeleteCandidate(candidate_id))
	
	if not success:
		raise HTTPException(status_code=500, detail="Failed to delete candidate")
	
	return CandidateDeleteResponse(
		message="Candidate deleted successfully",
		candidate_id=candidate_id
	)


@router.delete("/cvs/{candidate_cv_id}", response_model=CandidateCVDeleteResponse, summary="Delete Candidate CV")
async def delete_candidate_cv(
	candidate_cv_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Delete a specific candidate CV.
	
	This will permanently delete:
	- The CV file from storage
	- The CV record from the database
	- Update the candidate's latest_cv_id if this was the latest CV
	
	This action cannot be undone.
	"""
	# First check if CV exists
	cv = handle_query(db, GetCandidateCV(candidate_cv_id))
	if not cv:
		raise HTTPException(status_code=404, detail="Candidate CV not found")
	
	candidate_id = cv.candidate_id
	
	# Delete CV using CQRS
	success = handle_command(db, DeleteCandidateCV(candidate_cv_id))
	
	if not success:
		raise HTTPException(status_code=500, detail="Failed to delete candidate CV")
	
	return CandidateCVDeleteResponse(
		message="Candidate CV deleted successfully",
		candidate_cv_id=candidate_cv_id,
		candidate_id=candidate_id
	)


@router.post("/upload", response_model=List[CandidateUploadResponse], summary="Upload CV files (multipart)")
async def upload_cv_files(
	files: List[UploadFile] = File(..., description="CV files to upload"),
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Upload multiple CV files with deduplication and versioning.
	
	Accepts multiple files in a single request and returns per-file results.
	Files are deduplicated by SHA256 hash globally.
	Each candidate gets auto-incrementing CV versions.
	"""
	if not files:
		raise HTTPException(status_code=400, detail="No files provided")
	
	if len(files) > 10:  # Reasonable limit
		raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files per request.")
	
	results = []
	
	for file in files:
		try:
			# Validate file
			if not file.filename:
				results.append(CandidateUploadResponse(
					candidate_id="",
					cv_id="",
					file_name="",
					file_hash="",
					version=0,
					s3_url="",
					status="error",
					is_new_candidate=False,
					is_new_cv=False,
					cv_text=None,
					error="No filename provided"
				))
				continue
			
			# Check file size (10MB limit)
			file_content = await file.read()
			if len(file_content) > 10 * 1024 * 1024:
				results.append(CandidateUploadResponse(
					candidate_id="",
					cv_id="",
					file_name=file.filename,
					file_hash="",
					version=0,
					s3_url="",
					status="error",
					is_new_candidate=False,
					is_new_cv=False,
					cv_text=None,
					error="File size exceeds 10MB limit"
				))
				continue
			
			# Create upload command
			command = UploadCVFile(
				file_bytes=file_content,
				filename=file.filename,
				candidate_info={}  # No additional info provided
			)
			
			# Process upload
			result = handle_command(db, command)
			
			# Convert to response format
			upload_response = CandidateUploadResponse(
				candidate_id=result.get("candidate_id", ""),
				cv_id=result.get("cv_id", ""),
				file_name=file.filename,
				file_hash=result.get("file_hash", ""),
				version=result.get("version", 0),
				s3_url=result.get("s3_url", ""),
				status=result.get("status", "error"),
				is_new_candidate=result.get("is_new_candidate", False),
				is_new_cv=result.get("is_new_cv", False),
				cv_text=result.get("cv_text"),
				error=result.get("error")
			)
			
			results.append(upload_response)
			
		except Exception as e:
			# Handle unexpected errors
			results.append(CandidateUploadResponse(
				candidate_id="",
				cv_id="",
				file_name=file.filename if file.filename else "unknown",
				file_hash="",
				version=0,
				s3_url="",
				status="error",
				is_new_candidate=False,
				is_new_cv=False,
				cv_text=None,
				error=f"Unexpected error: {str(e)}"
			))
	
	return results


@router.post("/upload-legacy", response_model=List[CandidateRead], summary="Upload candidate CVs (legacy JSON)")
async def upload_cvs_legacy(payloads: List[CandidateCreate], db: Session = Depends(db_session)):
	"""Legacy endpoint for JSON-based candidate uploads."""
	models = handle_command(db, UploadCVs([p.model_dump() for p in payloads]))
	return [
		CandidateRead(
			id=m.id,
			full_name=m.full_name,
			email=m.email,
			phone=m.phone,
			latest_cv_id=m.latest_cv_id,
			created_at=m.created_at,
			updated_at=m.updated_at,
			cvs=None  # Not loading CVs in legacy endpoint
		)
		for m in models
	]


class ScorePayload(BaseException):
	candidate_ids: List[str]
	persona_id: str
	persona_weights: Dict[str, float]
	per_candidate_scores: Dict[str, Dict[str, float]]


@router.post("/score", summary="Score candidates (command)")
async def score_candidates(body: dict, db: Session = Depends(db_session)):
	candidate_ids = body.get("candidate_ids", [])
	persona_id = body.get("persona_id")
	persona_weights = body.get("persona_weights", {})
	per_candidate_scores = body.get("per_candidate_scores", {})
	rows = handle_command(db, ScoreCandidates(candidate_ids, persona_id, persona_weights, per_candidate_scores))
	return {"count": len(rows)}
