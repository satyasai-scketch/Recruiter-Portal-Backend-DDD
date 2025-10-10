from typing import List, Dict

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.schemas.candidate import CandidateCreate, CandidateRead, CandidateUploadResponse
from app.cqrs.handlers import UploadCVs, ScoreCandidates, handle_command
from app.cqrs.commands.upload_cv_file import UploadCVFile

router = APIRouter()


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
