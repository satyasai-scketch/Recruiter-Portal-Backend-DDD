from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db, get_current_user
from app.schemas.jd import JDCreate, JDRead, JDDocumentUpload, JDDocumentUploadResponse
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.jd_commands import (
	CreateJobDescription,
	ApplyJDRefinement,
	UpdateJobDescription,
)
from app.cqrs.commands.upload_jd_document import UploadJobDescriptionDocument
from app.cqrs.queries.jd_queries import (
	ListJobDescriptions,
	ListAllJobDescriptions,
	GetJobDescription,
)
from app.utils.error_handlers import handle_service_errors, rollback_on_error

router = APIRouter()

def _convert_jd_model_to_read_schema(jd_model) -> JDRead:
    """Convert JobDescriptionModel to JDRead schema with role_name."""
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


@router.get("/", response_model=list[JDRead], summary="List all Job Descriptions (no user filter)")
async def list_all_jds(db: Session = Depends(get_db), user=Depends(get_current_user)):
	"""
	List all job descriptions in the system.
	
	This endpoint returns all job descriptions regardless of who created them.
	No user-based filtering is applied.
	"""
	try:
		models = handle_query(db, ListAllJobDescriptions())
		return [_convert_jd_model_to_read_schema(m) for m in models]
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.post("/", response_model=JDRead, summary="Create job description (command)")
async def create_jd(payload: JDCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
	try:
		data = payload.model_dump()
		data["created_by"] = user.id
		model = handle_command(db, CreateJobDescription(data))
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
	- file: Document file (PDF, DOCX, or DOC, max 10MB)
	"""
	import logging
	logger = logging.getLogger(__name__)
	
	try:
		logger.info(f"=== JD DOCUMENT UPLOAD START ===")
		logger.info(f"User ID: {user.id}")
		logger.info(f"Title: {title}")
		logger.info(f"Role ID: {role_id}")
		logger.info(f"Company ID: {company_id}")
		logger.info(f"Notes: {notes}")
		logger.info(f"Tags: {tags}")
		logger.info(f"File object: {file}")
		logger.info(f"File filename: '{file.filename}'")
		logger.info(f"File content_type: {file.content_type}")
		logger.info(f"File size: {file.size if hasattr(file, 'size') else 'Unknown'}")
		# Validate file
		logger.info(f"Step 1: Validating file...")
		if not file.filename:
			logger.error("No filename provided")
			raise HTTPException(status_code=400, detail="No file provided")
		
		logger.info(f"Step 2: Reading file content...")
		# Check file size (10MB limit)
		file_content = await file.read()
		logger.info(f"File content read successfully. Size: {len(file_content)} bytes")
		
		if len(file_content) > 10 * 1024 * 1024:
			logger.error(f"File size {len(file_content)} exceeds 10MB limit")
			raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
		
		# Parse tags from JSON string
		logger.info(f"Step 3: Parsing tags...")
		import json
		try:
			tags_list = json.loads(tags) if tags else []
			if not isinstance(tags_list, list):
				raise ValueError("Tags must be a list")
			logger.info(f"Tags parsed successfully: {tags_list}")
		except (json.JSONDecodeError, ValueError) as e:
			logger.error(f"Tags parsing failed: {e}")
			raise HTTPException(status_code=400, detail="Invalid tags format. Must be a JSON array.")
		
		# Prepare payload
		logger.info(f"Step 4: Preparing payload...")
		payload = {
			"title": title.strip(),
			"role_id": role_id.strip(),
			"notes": notes.strip() if notes else None,
			"company_id": company_id.strip() if company_id else None,
			"tags": tags_list,
			"created_by": user.id
		}
		logger.info(f"Payload prepared: {payload}")
		
		# Process document upload
		logger.info(f"Step 5: Creating UploadJobDescriptionDocument command...")
		logger.info(f"Command parameters - payload: {payload}, file_content size: {len(file_content)}, filename: '{file.filename}'")
		
		command = UploadJobDescriptionDocument(payload, file_content, file.filename)
		logger.info(f"Command created successfully: {command}")
		
		logger.info(f"Step 6: Executing handle_command...")
		model = handle_command(db, command)
		logger.info(f"Command executed successfully. Model ID: {model.id}")
		
		# Prepare response
		logger.info(f"Step 7: Preparing response...")
		extracted_metadata = {
			"original_filename": model.original_document_filename,
			"file_size": model.original_document_size,
			"file_extension": model.original_document_extension,
			"word_count": model.document_word_count,
			"character_count": model.document_character_count
		}
		logger.info(f"Extracted metadata: {extracted_metadata}")
		
		response = JDDocumentUploadResponse(
			id=model.id,
			title=model.title,
			role_id=model.role_id,
			role_name=model.job_role.name if model.job_role else "Unknown Role",
			original_text=model.original_text,
			extracted_metadata=extracted_metadata,
			message=f"Successfully uploaded and processed {file.filename}"
		)
		logger.info(f"Response prepared successfully")
		logger.info(f"=== JD DOCUMENT UPLOAD COMPLETED SUCCESSFULLY ===")
		return response
		
	except HTTPException as e:
		logger.error(f"HTTPException occurred: {e.detail}")
		raise
	except (ValueError, SQLAlchemyError) as e:
		logger.error(f"ValueError/SQLAlchemyError occurred: {str(e)}")
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)
	except Exception as e:
		logger.error(f"Unexpected error occurred: {str(e)}")
		logger.error(f"Error type: {type(e).__name__}")
		import traceback
		logger.error(f"Traceback: {traceback.format_exc()}")
		rollback_on_error(db)
		raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


class JDRefinementRequest(JDCreate):
	refined_text: str


@router.post("/{jd_id}/refine", summary="Apply refined JD (command)")
async def refine_jd(jd_id: str, body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
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
    jd_id: str, 
    request: JDRefinementRequest,
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
        # Verify JD ownership
        jd = handle_query(db, GetJobDescription(jd_id))
        if not jd or jd.created_by != user.id:
            raise HTTPException(status_code=404, detail="JD not found")
        
        # Use company_id from request, or from JD, or None
        company_id = request.company_id or jd.company_id  # Can be None
        
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
async def get_jd(jd_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
	try:
		model = handle_query(db, GetJobDescription(jd_id))
		if not model or model.created_by != user.id:
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
    jd_id: str,
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
        # Verify JD ownership
        jd = handle_query(db, GetJobDescription(jd_id))
        if not jd or jd.created_by != user.id:
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
    jd_id: str,
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
        # Verify JD ownership
        jd = handle_query(db, GetJobDescription(jd_id))
        if not jd or jd.created_by != user.id:
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
async def update_jd(jd_id: str, body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
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
		# First check if JD exists and belongs to user
		model = handle_query(db, GetJobDescription(jd_id))
		if not model or model.created_by != user.id:
			raise HTTPException(status_code=404, detail="JD not found")
		# Then update using command handler
		updated = handle_command(db, UpdateJobDescription(jd_id, body, user.id))
		return _convert_jd_model_to_read_schema(updated)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)
