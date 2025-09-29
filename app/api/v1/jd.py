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
	GetJobDescription,
)
from app.utils.error_handlers import handle_service_errors, rollback_on_error

router = APIRouter()


@router.get("/", response_model=list[JDRead], summary="List all Job Descriptions (query)")
async def list_all_jds(db: Session = Depends(get_db), user=Depends(get_current_user)):
	try:
		models = handle_query(db, ListJobDescriptions(user.id))
		return [JDRead.model_validate(m) for m in models]
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
		return JDRead.model_validate(model)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.post("/upload-document", response_model=JDDocumentUploadResponse, summary="Upload job description document (command)")
async def upload_jd_document(
	title: str = Form(..., min_length=1, max_length=200),
	role: str = Form(..., min_length=1, max_length=100),
	notes: str = Form(None),
	company_id: str = Form(None),
	tags: str = Form("[]"),  # JSON string
	file: UploadFile = File(...),
	db: Session = Depends(get_db),
	user=Depends(get_current_user)
):
	"""
	Upload a job description document (PDF/DOCX) and extract text.
	
	The endpoint accepts:
	- title: Job title (required)
	- role: Job role/position (required) 
	- notes: Additional notes (optional)
	- company_id: Company identifier (optional)
	- tags: JSON array of tags (optional, defaults to empty array)
	- file: Document file (PDF or DOCX, max 10MB)
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
		
		# Prepare payload
		payload = {
			"title": title.strip(),
			"role": role.strip(),
			"notes": notes.strip() if notes else None,
			"company_id": company_id.strip() if company_id else None,
			"tags": tags_list,
			"created_by": user.id
		}
		
		# Process document upload
		model = handle_command(db, UploadJobDescriptionDocument(payload, file_content, file.filename))
		
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
			role=model.role,
			original_text=model.original_text,
			extracted_metadata=extracted_metadata,
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


@router.get("/{jd_id}", response_model=JDRead, summary="Retrieve full Job Description (query)")
async def get_jd(jd_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
	try:
		model = handle_query(db, GetJobDescription(jd_id))
		if not model or model.created_by != user.id:
			raise HTTPException(status_code=404, detail="JD not found")
		return JDRead.model_validate(model)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.patch("/{jd_id}", response_model=JDRead, summary="Update Job Description (selected_version, selected_text, selected_version, selected_edited.)")
async def update_jd(jd_id: str, body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
	try:
		# First check if JD exists and belongs to user
		model = handle_query(db, GetJobDescription(jd_id))
		if not model or model.created_by != user.id:
			raise HTTPException(status_code=404, detail="JD not found")
		# Then update using command handler
		updated = handle_command(db, UpdateJobDescription(jd_id, body))
		return JDRead.model_validate(updated)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)
