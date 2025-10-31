from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.schemas.candidate import (
	CandidateCreate, 
	CandidateUpdate,
	CandidateRead, 
	CandidateUploadResponse,
	CandidateListResponse,
	CandidateCVUpdate,
	CandidateCVRead,
	CandidateCVListResponse,
	CandidateDeleteResponse,
	CandidateCVDeleteResponse
)
from app.schemas.score import (
	ScorePayload, ScoreResponse, CandidateScoreRead, ScoreListResponse,
	ScoreStageRead, ScoreCategoryRead, ScoreSubcategoryRead, ScoreInsightRead
)
from app.cqrs.handlers import UploadCVs, ScoreCandidate, handle_command, handle_query
from app.cqrs.commands.upload_cv_file import UploadCVFile
from app.cqrs.commands.candidate_commands import UpdateCandidate, UpdateCandidateCV, DeleteCandidate, DeleteCandidateCV
from app.cqrs.queries.candidate_queries import (
	GetCandidate,
	ListAllCandidates,
	GetCandidateCV,
	GetCandidateCVs
)
from app.cqrs.queries.score_queries import (
	GetCandidateScore,
	ListCandidateScores,
	ListScoresForCandidatePersona,
	ListScoresForCVPersona,
	ListLatestCandidateScoresPerPersona,
	ListAllScores
)
from app.cqrs.commands.score_with_ai import ScoreCandidateWithAI
import time
from app.cqrs.queries.persona_queries import GetPersona
from app.cqrs.queries.jd_queries import GetJobDescription
from app.cqrs.queries.job_role_queries import GetJobRole

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


def _convert_score_stage_to_read_schema(stage_model) -> ScoreStageRead:
	"""Convert ScoreStageModel to ScoreStageRead schema format."""
	return ScoreStageRead(
		id=stage_model.id,
		candidate_score_id=stage_model.candidate_score_id,
		stage_number=stage_model.stage_number,
		method=stage_model.method,
		model=stage_model.model,
		score=float(stage_model.score),
		threshold=float(stage_model.threshold) if stage_model.threshold else None,
		min_threshold=float(stage_model.min_threshold) if stage_model.min_threshold else None,
		decision=stage_model.decision,
		reason=stage_model.reason,
		next_stage=stage_model.next_stage,
		relevance_score=stage_model.relevance_score,
		quick_assessment=stage_model.quick_assessment,
		skills_detected=stage_model.skills_detected,
		roles_detected=stage_model.roles_detected,
		key_matches=stage_model.key_matches,
		key_gaps=stage_model.key_gaps
	)


def _convert_score_subcategory_to_read_schema(subcat_model) -> ScoreSubcategoryRead:
	"""Convert ScoreSubcategoryModel to ScoreSubcategoryRead schema format."""
	return ScoreSubcategoryRead(
		id=subcat_model.id,
		category_id=subcat_model.category_id,
		subcategory_name=subcat_model.subcategory_name,
		weight_percentage=subcat_model.weight_percentage,
		expected_level=subcat_model.expected_level,
		actual_level=subcat_model.actual_level,
		base_score=float(subcat_model.base_score),
		missing_count=subcat_model.missing_count,
		scored_percentage=float(subcat_model.scored_percentage),
		notes=subcat_model.notes
	)


def _convert_score_category_to_read_schema(cat_model) -> ScoreCategoryRead:
	"""Convert ScoreCategoryModel to ScoreCategoryRead schema format."""
	return ScoreCategoryRead(
		id=cat_model.id,
		candidate_score_id=cat_model.candidate_score_id,
		category_name=cat_model.category_name,
		weight_percentage=cat_model.weight_percentage,
		category_score_percentage=float(cat_model.category_score_percentage),
		category_contribution=float(cat_model.category_contribution),
		subcategories=[_convert_score_subcategory_to_read_schema(sub) for sub in cat_model.subcategories]
	)


def _convert_score_insight_to_read_schema(insight_model) -> ScoreInsightRead:
	"""Convert ScoreInsightModel to ScoreInsightRead schema format."""
	return ScoreInsightRead(
		id=insight_model.id,
		candidate_score_id=insight_model.candidate_score_id,
		insight_type=insight_model.insight_type,
		insight_text=insight_model.insight_text
	)


def _convert_candidate_score_to_read_schema(score_model, db: Session = None) -> CandidateScoreRead:
	"""Convert CandidateScoreModel to CandidateScoreRead schema format."""
	# Fetch candidate and CV information if db session is provided
	candidate_name = None
	file_name = None
	persona_name = None
	role_name = None
	
	if db:
		try:
			candidate = handle_query(db, GetCandidate(score_model.candidate_id))
			cv = handle_query(db, GetCandidateCV(score_model.cv_id))
			candidate_name = candidate.full_name if candidate else None
			file_name = cv.file_name if cv else None
			
			# Fetch persona and role information
			persona = handle_query(db, GetPersona(score_model.persona_id))
			persona_name = persona.name if persona else None
			
			if persona:
				# Try to get role name from persona's role_name field first
				if persona.role_name:
					role_name = persona.role_name
				# If not available, get it from the job description's job role
				elif persona.job_description_id:
					job_description = handle_query(db, GetJobDescription(persona.job_description_id))
					if job_description and job_description.role_id:
						job_role = handle_query(db, GetJobRole(job_description.role_id))
						if job_role:
							role_name = job_role.name
		except Exception:
			# If there's an error fetching the data, continue without it
			pass
	
	return CandidateScoreRead(
		id=score_model.id,
		candidate_id=score_model.candidate_id,
		persona_id=score_model.persona_id,
		cv_id=score_model.cv_id,
		pipeline_stage_reached=score_model.pipeline_stage_reached,
		final_score=float(score_model.final_score),
		final_decision=score_model.final_decision,
		embedding_score=float(score_model.embedding_score) if score_model.embedding_score else None,
		lightweight_llm_score=float(score_model.lightweight_llm_score) if score_model.lightweight_llm_score else None,
		detailed_llm_score=float(score_model.detailed_llm_score) if score_model.detailed_llm_score else None,
		scored_at=score_model.scored_at,
		scoring_version=score_model.scoring_version,
		processing_time_ms=score_model.processing_time_ms,
		candidate_name=candidate_name,
		file_name=file_name,
		persona_name=persona_name,
		role_name=role_name,
		score_stages=[_convert_score_stage_to_read_schema(stage) for stage in score_model.score_stages],
		categories=[_convert_score_category_to_read_schema(cat) for cat in score_model.categories],
		insights=[_convert_score_insight_to_read_schema(insight) for insight in score_model.insights]
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


@router.patch("/{candidate_id}", response_model=CandidateRead, summary="Update Candidate")
async def update_candidate(
	candidate_id: str,
	update_data: CandidateUpdate,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Update candidate information.
	
	Only provided fields will be updated. Fields not included in the request will remain unchanged.
	"""
	# Convert Pydantic model to dict, excluding None values
	update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
	
	if not update_dict:
		raise HTTPException(status_code=400, detail="No fields provided for update")
	
	# Update candidate using CQRS
	updated_candidate = handle_command(db, UpdateCandidate(candidate_id, update_dict))
	
	if not updated_candidate:
		raise HTTPException(status_code=404, detail="Candidate not found")
	
	# Load CVs for this candidate
	cvs = handle_query(db, GetCandidateCVs(candidate_id))
	
	# Convert to response format with CVs included
	candidate_read = _convert_candidate_model_to_read_schema(updated_candidate)
	candidate_read.cvs = [_convert_cv_model_to_read_schema(cv) for cv in cvs]
	
	return candidate_read


@router.patch("/cvs/{candidate_cv_id}", response_model=CandidateCVRead, summary="Update Candidate CV")
async def update_candidate_cv(
	candidate_cv_id: str,
	update_data: CandidateCVUpdate,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Update candidate CV information.
	
	Only provided fields will be updated. Fields not included in the request will remain unchanged.
	"""
	# Convert Pydantic model to dict, excluding None values
	update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
	
	if not update_dict:
		raise HTTPException(status_code=400, detail="No fields provided for update")
	
	# Update CV using CQRS
	updated_cv = handle_command(db, UpdateCandidateCV(candidate_cv_id, update_dict))
	
	if not updated_cv:
		raise HTTPException(status_code=404, detail="Candidate CV not found")
	
	return _convert_cv_model_to_read_schema(updated_cv)


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


@router.post("/score", response_model=ScoreResponse, summary="Score candidate against persona (comprehensive)")
async def score_candidate(body: ScorePayload, db: Session = Depends(db_session)):
	score = handle_command(db, ScoreCandidate(
		candidate_id=body.candidate_id,
		persona_id=body.persona_id,
		cv_id=body.cv_id,
		ai_scoring_response=body.ai_scoring_response,
		scoring_version=body.scoring_version,
		processing_time_ms=body.processing_time_ms
	))
	
	# Fetch candidate and CV information for the response
	candidate = handle_query(db, GetCandidate(body.candidate_id))
	cv = handle_query(db, GetCandidateCV(body.cv_id))
	
	# Fetch persona and role information for the response
	persona = handle_query(db, GetPersona(body.persona_id))
	persona_name = persona.name if persona else None
	role_name = None
	
	if persona:
		# Try to get role name from persona's role_name field first
		if persona.role_name:
			role_name = persona.role_name
		# If not available, get it from the job description's job role
		elif persona.job_description_id:
			job_description = handle_query(db, GetJobDescription(persona.job_description_id))
			if job_description and job_description.role_id:
				job_role = handle_query(db, GetJobRole(job_description.role_id))
				if job_role:
					role_name = job_role.name
	
	# Extract candidate name and file name
	candidate_name = candidate.full_name if candidate else None
	file_name = cv.file_name if cv else None
	
	return ScoreResponse(
		score_id=score.id,
		candidate_id=score.candidate_id,
		persona_id=score.persona_id,
		final_score=float(score.final_score),
		final_decision=score.final_decision,
		pipeline_stage_reached=score.pipeline_stage_reached,
		scored_at=score.scored_at,
		candidate_name=candidate_name,
		file_name=file_name,
		persona_name=persona_name,
		role_name=role_name
	)


@router.get("/scores/{score_id}", response_model=CandidateScoreRead, summary="Get Candidate Score by ID")
async def get_candidate_score(
	score_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get detailed scoring information for a specific score ID.
	"""
	score = handle_query(db, GetCandidateScore(score_id))
	
	if not score:
		raise HTTPException(status_code=404, detail="Score not found")
	
	# Check if the candidate still exists (to handle orphaned scores from deleted candidates)
	candidate = handle_query(db, GetCandidate(score.candidate_id))
	if not candidate:
		raise HTTPException(status_code=404, detail="Score not found - associated candidate has been deleted")
	
	# Convert to response format
	return _convert_candidate_score_to_read_schema(score, db)



@router.post("/score-with-ai", response_model=ScoreResponse, summary="Score candidate with AI")
async def score_candidate_with_ai(
    candidate_id: str,
    persona_id: str,
    cv_id: str,
    force_rescore: bool = Query(False, description="Force re-scoring even if a score already exists"),
    db: Session = Depends(db_session),
    user=Depends(get_current_user)
):
    """
    AI-powered automatic scoring with duplicate prevention.
    
    This endpoint checks if a score already exists for the given CV and persona combination.
    If a score exists, it returns the existing score instead of performing new AI scoring.
    Use force_rescore=True to bypass this check and force re-scoring.
    """
    # Ensure contextvars are set before calling sync handler
    # FastAPI preserves contextvars in async->sync calls, but we ensure they're set here
    from app.core.context import request_user_id, request_db_session
    request_user_id.set(user.id)
    request_db_session.set(db)
    
    start_time = time.time()
    
    try:
        # Check if a score already exists for this CV and persona combination
        # Skip this check if force_rescore is True
        if not force_rescore:
            existing_scores = handle_query(db, ListScoresForCVPersona(cv_id, persona_id, skip=0, limit=1))
            
            if existing_scores:
                # Return the existing score instead of creating a new one
                # This prevents duplicate AI scoring for the same CV-persona combination
                existing_score = existing_scores[0]
                
                # Fetch candidate and CV information for the response
                candidate = handle_query(db, GetCandidate(candidate_id))
                cv = handle_query(db, GetCandidateCV(cv_id))
                
                # Fetch persona and role information for the response
                persona = handle_query(db, GetPersona(persona_id))
                persona_name = persona.name if persona else None
                role_name = None
                
                if persona:
                    # Try to get role name from persona's role_name field first
                    if persona.role_name:
                        role_name = persona.role_name
                    # If not available, get it from the job description's job role
                    elif persona.job_description_id:
                        job_description = handle_query(db, GetJobDescription(persona.job_description_id))
                        if job_description and job_description.role_id:
                            job_role = handle_query(db, GetJobRole(job_description.role_id))
                            if job_role:
                                role_name = job_role.name
                
                # Extract candidate name and file name
                candidate_name = candidate.full_name if candidate else None
                file_name = cv.file_name if cv else None
                
                return ScoreResponse(
                    score_id=existing_score.id,
                    candidate_id=existing_score.candidate_id,
                    persona_id=existing_score.persona_id,
                    final_score=float(existing_score.final_score),
                    final_decision=existing_score.final_decision,
                    pipeline_stage_reached=existing_score.pipeline_stage_reached,
					scored_at=existing_score.scored_at,
                    candidate_name=candidate_name,
                    file_name=file_name,
                    persona_name=persona_name,
                    role_name=role_name
                )
        
        # No existing score found, proceed with AI scoring
        # Use command handler (like persona generation)
        ai_scoring_response = handle_command(db, ScoreCandidateWithAI(
            candidate_id=candidate_id,
            persona_id=persona_id,
            cv_id=cv_id
        ))
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to database
        score = handle_command(db, ScoreCandidate(
            candidate_id=candidate_id,
            persona_id=persona_id,
            cv_id=cv_id,
            ai_scoring_response=ai_scoring_response,
            scoring_version="v1.0",
            processing_time_ms=processing_time_ms
        ))
        
        # Fetch candidate and CV information for the response
        candidate = handle_query(db, GetCandidate(candidate_id))
        cv = handle_query(db, GetCandidateCV(cv_id))
        
        # Fetch persona and role information for the response
        persona = handle_query(db, GetPersona(persona_id))
        persona_name = persona.name if persona else None
        role_name = None
        
        if persona:
            # Try to get role name from persona's role_name field first
            if persona.role_name:
                role_name = persona.role_name
            # If not available, get it from the job description's job role
            elif persona.job_description_id:
                job_description = handle_query(db, GetJobDescription(persona.job_description_id))
                if job_description and job_description.role_id:
                    job_role = handle_query(db, GetJobRole(job_description.role_id))
                    if job_role:
                        role_name = job_role.name
        
        # Extract candidate name and file name
        candidate_name = candidate.full_name if candidate else None
        file_name = cv.file_name if cv else None
        
        return ScoreResponse(
            score_id=score.id,
            candidate_id=score.candidate_id,
            persona_id=score.persona_id,
            final_score=float(score.final_score),
            final_decision=score.final_decision,
            pipeline_stage_reached=score.pipeline_stage_reached,
            candidate_name=candidate_name,
            file_name=file_name,
            persona_name=persona_name,
            role_name=role_name,
			scored_at=score.scored_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/{candidate_id}/scores", response_model=ScoreListResponse, summary="Get Candidate Scores")
async def get_candidate_scores(
	candidate_id: str,
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	latest_only: bool = Query(True, description="Show only the latest score per persona"),
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get scores for a specific candidate.
	
	By default, returns only the latest score for each persona to avoid duplicates.
	Set latest_only=False to get all scores for the candidate.
	"""
	# First check if candidate exists
	candidate = handle_query(db, GetCandidate(candidate_id))
	if not candidate:
		raise HTTPException(status_code=404, detail="Candidate not found")
	
	skip = (page - 1) * size
	
	# Choose the appropriate query based on latest_only parameter
	if latest_only:
		scores = handle_query(db, ListLatestCandidateScoresPerPersona(candidate_id, skip, size))
	else:
		scores = handle_query(db, ListCandidateScores(candidate_id, skip, size))
	
	# Convert to response format
	score_reads = [_convert_candidate_score_to_read_schema(score, db) for score in scores]
	
	# Get total count (simplified for now)
	total = len(score_reads)  # This should be improved with proper counting
	
	return ScoreListResponse(
		scores=score_reads,
		total=total,
		page=page,
		size=size,
		has_next=(skip + size) < total,
		has_prev=page > 1
	)


@router.get("/{candidate_id}/scores/{persona_id}", response_model=ScoreListResponse, summary="Get Candidate Scores for Persona")
async def get_candidate_scores_for_persona(
	candidate_id: str,
	persona_id: str,
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get scores for a candidate against a specific persona.
	"""
	# First check if candidate exists
	candidate = handle_query(db, GetCandidate(candidate_id))
	if not candidate:
		raise HTTPException(status_code=404, detail="Candidate not found")
	
	skip = (page - 1) * size
	scores = handle_query(db, ListScoresForCandidatePersona(candidate_id, persona_id, skip, size))
	
	# Convert to response format
	score_reads = [_convert_candidate_score_to_read_schema(score, db) for score in scores]
	
	# Get total count (simplified for now)
	total = len(score_reads)  # This should be improved with proper counting
	
	return ScoreListResponse(
		scores=score_reads,
		total=total,
		page=page,
		size=size,
		has_next=(skip + size) < total,
		has_prev=page > 1
	)
