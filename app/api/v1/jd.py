from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db, get_current_user
from app.schemas.jd import JDCreate, JDRead
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.jd_commands import (
	CreateJobDescription,
	ApplyJDRefinement,
	UpdateJobDescription,
)
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
