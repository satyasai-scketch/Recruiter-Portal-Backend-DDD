from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db, get_current_user
from app.api.deps_authorization import get_accessible_jd_ids_dependency, require_jd_access
from app.schemas.jd import JDCreate, JDRead, JDDocumentUpload, JDDocumentUploadResponse, JDListResponse, JDListItem, PersonaListItem, JDDeleteResponse, HiringManagerInfo
from app.cqrs.handlers import handle_command, handle_query
from app.services.jd_service import JDService
from app.cqrs.commands.jd_commands import (
	CreateJobDescription,
	ApplyJDRefinement,
	UpdateJobDescription,
	DeleteJobDescription,
)
from app.cqrs.commands.upload_jd_document import UploadJobDescriptionDocument
from app.cqrs.queries.jd_queries import (
	ListJobDescriptions,
	ListAllJobDescriptions,
	GetJobDescription,
	CountJobDescriptions,
	ListJobDescriptionsByRoleId,
)
from app.utils.error_handlers import handle_service_errors, rollback_on_error

router = APIRouter()

def _convert_jd_model_to_read_schema(jd_model) -> JDRead:
    """Convert JobDescriptionModel to JDRead schema with role_name and hiring managers."""
    # Fetch hiring managers from the mappings
    hiring_managers = []
    if hasattr(jd_model, 'hiring_manager_mappings') and jd_model.hiring_manager_mappings:
        for mapping in jd_model.hiring_manager_mappings:
            if mapping.hiring_manager:
                hm = mapping.hiring_manager
                hiring_managers.append(HiringManagerInfo(
                    id=hm.id,
                    first_name=hm.first_name,
                    last_name=hm.last_name,
                    email=hm.email,
                    full_name=f"{hm.first_name} {hm.last_name}".strip()
                ))
    
    return JDRead(
        id=jd_model.id,
        title=jd_model.title,
        role_id=jd_model.role_id,
        role_name=jd_model.job_role.name if jd_model.job_role else "Unknown Role",
        original_text=jd_model.original_text,
        refined_text=jd_model.refined_text,
        company_id=jd_model.company_id,
        notes=jd_model.notes,
        tags=jd_model.tags or [],
        hiring_managers=hiring_managers,
        selected_version=jd_model.selected_version,
        selected_text=jd_model.selected_text,
        selected_edited=jd_model.selected_edited,
        created_at=jd_model.created_at,
        created_by=jd_model.created_by,
        updated_at=jd_model.updated_at,
        updated_by=jd_model.updated_by,
        # Document metadata fields
        original_document_filename=jd_model.original_document_filename,
        original_document_size=jd_model.original_document_size,
        original_document_extension=jd_model.original_document_extension,
        document_word_count=jd_model.document_word_count,
        document_character_count=jd_model.document_character_count
    )


def _convert_jd_model_to_list_item(jd_model) -> JDListItem:
    """Convert JobDescriptionModel to JDListItem schema (optimized for list view, excludes text fields)."""
    # Build personas array
    personas = [
        PersonaListItem(
            persona_id=p.id,
            persona_name=p.name
        )
        for p in (jd_model.personas or [])
    ]
    
    # Get creator name
    creator_name = None
    if jd_model.creator:
        creator_name = f"{jd_model.creator.first_name} {jd_model.creator.last_name}".strip()
    
    # Get updater name
    updater_name = None
    if jd_model.updater:
        updater_name = f"{jd_model.updater.first_name} {jd_model.updater.last_name}".strip()
    
    return JDListItem(
        id=jd_model.id,
        title=jd_model.title,
        role_id=jd_model.role_id,
        role_name=jd_model.job_role.name if jd_model.job_role else "Unknown Role",
        company_id=jd_model.company_id,
        notes=jd_model.notes,
        tags=jd_model.tags or [],
        selected_version=jd_model.selected_version,
        selected_edited=jd_model.selected_edited,
        created_at=jd_model.created_at,
        created_by=jd_model.created_by,
        created_by_name=creator_name,
        updated_at=jd_model.updated_at,
        updated_by=jd_model.updated_by,
        updated_by_name=updater_name,
        # Document metadata fields
        original_document_filename=jd_model.original_document_filename,
        original_document_size=jd_model.original_document_size,
        original_document_extension=jd_model.original_document_extension,
        document_word_count=jd_model.document_word_count,
        document_character_count=jd_model.document_character_count,
        # Personas array
        personas=personas
        # Note: original_text, refined_text, selected_text are intentionally excluded
    )


@router.get("/", response_model=JDListResponse, summary="List all Job Descriptions with pagination (role-based access)")
async def list_all_jds(
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	List job descriptions accessible to the current user with pagination.
	
	Access rules:
	- Admin/Recruiter: Can see all job descriptions
	- Hiring Manager: Can only see JDs they created or are assigned to
	
	Uses optimized SQL filtering directly in database instead of fetching all accessible IDs first.
	"""
	try:
		skip = (page - 1) * size
		
		# Use service with access filtering (pass user directly for optimized SQL filtering)
		jd_service = JDService()
		models = jd_service.list_all_optimized(db, skip, size, user)
		
		# Get total count with access filtering
		total = jd_service.count(db, user)
		
		# Convert models to list items
		jd_reads = [_convert_jd_model_to_list_item(m) for m in models]
		
		# Build response
		response = JDListResponse(
			jds=jd_reads,
			total=total,
			page=page,
			size=size,
			has_next=(skip + size) < total,
			has_prev=page > 1
		)
		
		return response
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.get("/by-role/{role_id}", response_model=JDListResponse, summary="List Job Descriptions by Role ID")
async def list_jds_by_role_id(
	role_id: str,
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	List job descriptions filtered by role_id with pagination.
	
	This endpoint returns all job descriptions that match the given role_id.
	The results are paginated and use optimized queries (excluding large text fields).
	
	Args:
		role_id: The job role ID to filter by
		page: Page number (default: 1)
		size: Page size (default: 10, max: 100)
	"""
	try:
		skip = (page - 1) * size
		
		# Query job descriptions by role_id
		models = handle_query(db, ListJobDescriptionsByRoleId(role_id, skip, size, optimized=True))
		
		# Count total job descriptions for this role_id
		# We need to count separately since we're filtering by role_id
		from app.db.models.job_description import JobDescriptionModel
		from sqlalchemy import func
		total = db.query(func.count(JobDescriptionModel.id)).filter(
			JobDescriptionModel.role_id == role_id
		).scalar() or 0
		
		# Convert models to list items
		jd_reads = [_convert_jd_model_to_list_item(m) for m in models]
		
		# Build response
		response = JDListResponse(
			jds=jd_reads,
			total=total,
			page=page,
			size=size,
			has_next=(skip + size) < total,
			has_prev=page > 1
		)
		
		return response
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.post("/", response_model=JDRead, summary="Create job description (command)")
async def create_jd(payload: JDCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
	"""
	Create a new job description.
	
	The endpoint accepts:
	- title: Job title (required)
	- role_id: Job role ID (required)
	- original_text: Job description text (required)
	- company_id: Company identifier (optional)
	- notes: Additional notes (optional)
	- tags: List of tags (optional)
	- hiring_manager_ids: List of hiring manager user IDs (optional)
	- selected_version: Selected version (optional)
	- selected_text: Selected text (optional)
	- selected_edited: Whether selected text was edited (optional)
	"""
	try:
		data = payload.model_dump()
		data["created_by"] = user.id
		model = handle_command(db, CreateJobDescription(data))
		
		# Eager load hiring manager relationships
		from sqlalchemy.orm import joinedload
		from app.db.models.job_description import JobDescriptionModel
		from app.db.models.jd_hiring_manager import JDHiringManagerMappingModel
		
		# Reload the model with relationships
		model = (
			db.query(JobDescriptionModel)
			.options(
				joinedload(JobDescriptionModel.hiring_manager_mappings).joinedload(JDHiringManagerMappingModel.hiring_manager),
				joinedload(JobDescriptionModel.job_role)
			)
			.filter(JobDescriptionModel.id == model.id)
			.first()
		)
		
		return _convert_jd_model_to_read_schema(model)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.post("/upload-document", response_model=JDDocumentUploadResponse, summary="Upload job description document (command)")
async def upload_jd_document(
	title: str = Form(..., min_length=1, max_length=200),
	role_id: str = Form(..., description="Job role ID"),
	notes: str = Form(None),
	company_id: str = Form(None),
	tags: str = Form("[]"),  # JSON string
	hiring_manager_ids: str = Form("[]"),  # JSON string array of hiring manager IDs
	file: UploadFile = File(...),
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	Upload a job description document (PDF/DOCX/DOC) and extract text.
	
	The endpoint accepts:
	- title: Job title (required)
	- role_id: Job role ID (required) 
	- notes: Additional notes (optional)
	- company_id: Company identifier (optional)
	- tags: JSON array of tags (optional, defaults to empty array)
	- hiring_manager_ids: JSON array of hiring manager user IDs (optional, defaults to empty array)
	- file: Document file (PDF, DOCX, or DOC, max 10MB)
	"""
	try:
		# Validate file
		if not file.filename:
			raise HTTPException(status_code=400, detail="No file provided")
		
		# Check file size (10MB limit)
		file_content = await file.read()
		if len(file_content) > 10 * 1024 * 1024:
			raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
		
		# Parse tags from JSON string
		import json
		try:
			tags_list = json.loads(tags) if tags else []
			if not isinstance(tags_list, list):
				raise ValueError("Tags must be a list")
		except (json.JSONDecodeError, ValueError):
			raise HTTPException(status_code=400, detail="Invalid tags format. Must be a JSON array.")
		
		# Parse hiring_manager_ids from JSON string
		# Try to handle various input formats for better user experience
		try:
			hm_ids_list = []
			if hiring_manager_ids and hiring_manager_ids.strip():
				try:
					# First, try parsing as JSON
					hm_ids_list = json.loads(hiring_manager_ids)
				except json.JSONDecodeError:
					# If JSON parsing fails, try to handle Python list format or comma-separated values
					# Remove brackets and quotes, then split by comma
					cleaned = hiring_manager_ids.strip()
					# Remove leading/trailing brackets if present
					if cleaned.startswith('[') and cleaned.endswith(']'):
						cleaned = cleaned[1:-1]
					# Split by comma and clean up each item
					hm_ids_list = [item.strip().strip("'\"") for item in cleaned.split(',') if item.strip()]
				
				# Validate the result
				if not isinstance(hm_ids_list, list):
					raise ValueError("hiring_manager_ids must be a list")
				# Validate that all items are strings and not empty
				hm_ids_list = [str(hm_id).strip() for hm_id in hm_ids_list if str(hm_id).strip()]
				if not all(hm_id for hm_id in hm_ids_list):
					raise ValueError("All hiring_manager_ids must be non-empty strings")
		except ValueError as e:
			raise HTTPException(status_code=400, detail=f"Invalid hiring_manager_ids format. Must be a JSON array of strings or comma-separated values. Error: {str(e)}")
		
		# Prepare payload
		payload = {
			"title": title.strip(),
			"role_id": role_id.strip(),
			"notes": notes.strip() if notes else None,
			"company_id": company_id.strip() if company_id else None,
			"tags": tags_list,
			"hiring_manager_ids": hm_ids_list,
			"created_by": user.id
		}
		
		# Process document upload
		model = handle_command(db, UploadJobDescriptionDocument(payload, file_content, file.filename))
		
		# Eager load hiring manager relationships
		from sqlalchemy.orm import joinedload
		from app.db.models.job_description import JobDescriptionModel
		from app.db.models.jd_hiring_manager import JDHiringManagerMappingModel
		
		# Reload the model with relationships
		model = (
			db.query(JobDescriptionModel)
			.options(
				joinedload(JobDescriptionModel.hiring_manager_mappings).joinedload(JDHiringManagerMappingModel.hiring_manager),
				joinedload(JobDescriptionModel.job_role)
			)
			.filter(JobDescriptionModel.id == model.id)
			.first()
		)
		
		# Fetch hiring managers from the mappings
		hiring_managers = []
		if model and model.hiring_manager_mappings:
			for mapping in model.hiring_manager_mappings:
				if mapping.hiring_manager:
					hm = mapping.hiring_manager
					hiring_managers.append(HiringManagerInfo(
						id=hm.id,
						first_name=hm.first_name,
						last_name=hm.last_name,
						email=hm.email,
						full_name=f"{hm.first_name} {hm.last_name}".strip()
					))
		
		# Prepare response
		extracted_metadata = {
			"original_filename": model.original_document_filename,
			"file_size": model.original_document_size,
			"file_extension": model.original_document_extension,
			"word_count": model.document_word_count,
			"character_count": model.document_character_count
		}
		
		return JDDocumentUploadResponse(
			id=model.id,
			title=model.title,
			role_id=model.role_id,
			role_name=model.job_role.name if model.job_role else "Unknown Role",
			original_text=model.original_text,
			extracted_metadata=extracted_metadata,
			hiring_managers=hiring_managers,
			message=f"Successfully uploaded and processed {file.filename}"
		)
		
	except HTTPException:
		raise
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)
	except Exception as e:
		rollback_on_error(db)
		raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


class JDRefinementRequest(JDCreate):
	refined_text: str


@router.post("/{jd_id}/refine", summary="Apply refined JD (command)")
async def refine_jd(
	jd_id: str = Depends(require_jd_access),
	body: dict = None,
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	Apply refined JD text to a job description.
	
	Access rules:
	- Admin/Recruiter: Can refine any JD
	- Hiring Manager: Can only refine JDs they created or are assigned to
	"""
	try:
		refined_text = body.get("refined_text")
		if not refined_text:
			raise HTTPException(status_code=400, detail="'refined_text' is required")
		model = handle_command(db, ApplyJDRefinement(jd_id, refined_text))
		return {"id": model.id, "refined_text": model.refined_text}
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)

from app.schemas.jd import JDRefinementRequest, JDRefinementResponse
from app.cqrs.commands.refine_jd_with_ai import RefineJDWithAI

# ADD new endpoint (after the existing /refine endpoint)
@router.post("/{jd_id}/refine/ai", response_model=JDRefinementResponse, summary="AI-powered JD refinement")
async def refine_jd_with_ai(
    request: JDRefinementRequest,
    jd_id: str = Depends(require_jd_access), 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    """Refine job description using AI.
	 This endpoint refines a job description (JD) using AI, based on the provided parameters.
	 
	 Request Body (JDRefinementRequest):
	 - role (str): The job role/title for which the JD is being refined. Required.
	 - company_id (Optional[str]): The company ID to use for context. Optional; if not provided, the JD's company_id is used if available.
	 - methodology (str): The AI refinement methodology. Accepts:
	     - "direct": Directly refines the JD text using AI.
	     - "template_based": Uses a template-matching approach to refine the JD.
	   Default is "direct".
	 - min_similarity (Optional[float]): Minimum similarity threshold (between 0.0 and 1.0) for template matching. 
	   Only used if methodology is "template_based". Default is 0.5.
	
	 Response (JDRefinementResponse):
	 - jd_id (str): The ID of the refined JD.
	 - original_text (str): The original JD text before refinement.
	 - refined_text (str): The AI-refined JD text.
	 - improvements (List[str]): List of improvements or changes made by the AI.
	 - methodology (str): The methodology used for refinement ("direct" or "template_based").
	 - template_used (Optional[Dict[str, Any]]): If template-based, details of the template used (may be None).
	 - template_similarity (Optional[float]): If template-based, the similarity score with the template (may be None).
	
	 Example request:
	 {
	   "role": "Software Engineer",
	   "company_id": "abc123",
	   "methodology": "template_based",
	   "min_similarity": 0.8
	 }
	
	 Example response:
	 {
	   "jd_id": "jd_456",
	   "original_text": "...",
	   "refined_text": "...",
	   "improvements": ["Clarified responsibilities", "Added required skills section"],
	   "methodology": "template_based",
	   "template_used": {"id": "tpl_789", "name": "Standard SWE Template"},
	   "template_similarity": 0.85
	 }
	"""
    try:
        # Verify JD access (handled by require_jd_access dependency)
        jd = handle_query(db, GetJobDescription(jd_id))
        if not jd:
            raise HTTPException(status_code=404, detail="JD not found")
        
        # Use company_id from request, or from JD, or None
        company_id = request.company_id or jd.company_id  # Can be None
        
        # Ensure contextvars are set before calling sync handler
        # FastAPI preserves contextvars in async->sync calls, but we ensure they're set here
        from app.core.context import request_user_id, request_db_session
        request_user_id.set(user.id)
        request_db_session.set(db)
        
        # Execute refinement (now works with None company_id)
        updated_model, refinement_result = handle_command(
            db, 
            RefineJDWithAI(
                jd_id=jd_id,
                role=request.role,
                company_id=company_id,  # Pass None if not available
                methodology=request.methodology,
                min_similarity=request.min_similarity or 0.7
            )
        )
        
        return JDRefinementResponse(
            jd_id=updated_model.id,
            original_text=refinement_result.original_text,
            refined_text=refinement_result.refined_text,
            improvements=refinement_result.improvements,
            methodology=refinement_result.methodology,
            template_used=refinement_result.template_used,
            template_similarity=refinement_result.template_similarity
        )
        
    except (ValueError, SQLAlchemyError) as e:
        if isinstance(e, SQLAlchemyError):
            rollback_on_error(db)
        raise handle_service_errors(e)

@router.get("/{jd_id}", response_model=JDRead, summary="Retrieve full Job Description (query)")
async def get_jd(
	jd_id: str = Depends(require_jd_access),
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	Retrieve a specific job description.
	
	Access rules:
	- Admin/Recruiter: Can access any JD
	- Hiring Manager: Can only access JDs they created or are assigned to
	"""
	try:
		model = handle_query(db, GetJobDescription(jd_id))
		if not model:
			raise HTTPException(status_code=404, detail="JD not found")
		return _convert_jd_model_to_read_schema(model)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)

# Add import
from app.schemas.jd import JDDiffResponse
from app.cqrs.queries.jd_queries import GetJDDiff

# Add new endpoint
@router.get("/{jd_id}/diff", response_model=JDDiffResponse, summary="Get diff between original and refined JD")
async def get_jd_diff(
    jd_id: str = Depends(require_jd_access),
    format: str = "table",  # Query parameter: table, inline, or simple
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get HTML diff showing changes between original and refined JD.
    
    **Formats:**
    - `table` (default): Side-by-side comparison table
    - `inline`: Full HTML page with side-by-side view
    - `simple`: Inline markup with <ins> and <del> tags
    
    **Response includes:**
    - HTML diff with highlighted changes
    - Statistics (words added/removed, similarity ratio)
    """
    try:
        # Verify JD access (handled by require_jd_access dependency)
        jd = handle_query(db, GetJobDescription(jd_id))
        if not jd:
            raise HTTPException(status_code=404, detail="JD not found")
        
        # Get diff
        result = handle_query(db, GetJDDiff(jd_id, diff_format=format))
        
        return JDDiffResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (SQLAlchemyError) as e:
        rollback_on_error(db)
        raise handle_service_errors(e)
from app.schemas.jd import JDInlineMarkupResponse
from app.cqrs.queries.jd_queries import GetJDInlineMarkup
@router.get("/{jd_id}/markup", response_model=JDInlineMarkupResponse, summary="Get inline markup for original and refined JD")
async def get_jd_inline_markup(
    jd_id: str = Depends(require_jd_access),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get original and refined JD texts with inline markup highlighting changes.

    **Response includes:**
    - `original_text`: Text with deletions highlighted in red with strikethrough
    - `refined_text`: Text with additions highlighted in green
    - `stats`: Change statistics
    """
    try:
        # Verify JD access (handled by require_jd_access dependency)
        jd = handle_query(db, GetJobDescription(jd_id))
        if not jd:
            raise HTTPException(status_code=404, detail="JD not found")

        # Get inline markup
        result = handle_query(db, GetJDInlineMarkup(jd_id))

        return JDInlineMarkupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except SQLAlchemyError as e:
        rollback_on_error(db)
        raise handle_service_errors(e)

@router.patch("/{jd_id}", response_model=JDRead, summary="Update Job Description (selected_version, selected_text, selected_version, selected_edited.)")
async def update_jd(
	jd_id: str = Depends(require_jd_access),
	body: dict = None,
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	Update a job description (JD) with the provided fields.
	
	Request Body (dict):
	- selected_version (Optional[str]): The version of the JD Recruiter selected:
		- "original"
		- "refined"
	- selected_text (Optional[str]): The text of the JD Recruiter selected finally.
	- selected_edited (Optional[bool]): Whether the JD Recruiter selected finally has been edited:
		- True
		- False
	
	"""
	try:
		# Verify JD access (handled by require_jd_access dependency)
		model = handle_query(db, GetJobDescription(jd_id))
		if not model:
			raise HTTPException(status_code=404, detail="JD not found")
		# Then update using command handler
		updated = handle_command(db, UpdateJobDescription(jd_id, body, user.id))
		return _convert_jd_model_to_read_schema(updated)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.delete("/{jd_id}", response_model=JDDeleteResponse, summary="Delete Job Description")
async def delete_jd(
	jd_id: str = Depends(require_jd_access),
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	Delete a job description and all associated data.
	
	This will delete:
	- All personas associated with this JD
	- All candidate scores evaluated against those personas
	- The job description itself
	
	Access rules:
	- Admin/Recruiter: Can delete any JD
	- Hiring Manager: Can only delete JDs they created or are assigned to
	
	Note: This operation cannot be undone.
	"""
	try:
		# JD access is verified by require_jd_access dependency
		# First check if JD exists
		model = handle_query(db, GetJobDescription(jd_id))
		if not model:
			raise HTTPException(status_code=404, detail="Job description not found")
		
		# Delete using command handler
		result = handle_command(db, DeleteJobDescription(jd_id))
		
		return JDDeleteResponse(
			message=result["message"],
			jd_id=result["jd_id"],
			personas_deleted=result["personas_deleted"],
			scores_deleted=result["scores_deleted"]
		)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)
