from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import db_session, get_db
from app.schemas.jd import JDCreate, JDRead
from app.cqrs.handlers import (
	CreateJobDescription,
	ApplyJDRefinement,
	handle_command,
)
from app.services.jd_service import JDService
from app.utils.error_handlers import handle_service_errors, rollback_on_error

router = APIRouter()


@router.get("/", response_model=list[JDRead], summary="List all Job Descriptions (query)")
async def list_all_jds(db: Session = Depends(get_db)):
	try:
		models = JDService().list_all(db)
		return [
			JDRead(
				id=m.id,
				title=m.title,
				role=m.role,
				original_text=m.original_text,
				refined_text=m.refined_text,
				company_id=m.company_id,
				notes=m.notes,
				tags=m.tags or [],
				final_text=m.final_text,
			)
			for m in models
		]
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.post("/", response_model=JDRead, summary="Create job description (command)")
async def create_jd(payload: JDCreate, db: Session = Depends(get_db)):
	try:
		model = handle_command(db, CreateJobDescription(payload.dict()))
		return JDRead(
			id=model.id,
			title=model.title,
			role=model.role,
			original_text=model.original_text,
			refined_text=model.refined_text,
			company_id=model.company_id,
			notes=model.notes,
			tags=model.tags or [],
			final_text=None,
		)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


class JDRefinementRequest(JDCreate):
	refined_text: str


@router.post("/{jd_id}/refine", summary="Apply refined JD (command)")
async def refine_jd(jd_id: str, body: dict, db: Session = Depends(get_db)):
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
async def get_jd(jd_id: str, db: Session = Depends(get_db)):
	try:
		model = JDService().get_by_id(db, jd_id)
		if not model:
			raise HTTPException(status_code=404, detail="JD not found")
		return JDRead(
			id=model.id,
			title=model.title,
			role=model.role,
			original_text=model.original_text,
			refined_text=model.refined_text,
			company_id=model.company_id,
			notes=model.notes,
			tags=model.tags or [],
			final_text=model.final_text,
		)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)


@router.patch("/{jd_id}", response_model=JDRead, summary="Update Job Description (final_text, notes, tags, etc.)")
async def update_jd(jd_id: str, body: dict, db: Session = Depends(get_db)):
	try:
		service = JDService()
		model = service.get_by_id(db, jd_id)
		if not model:
			raise HTTPException(status_code=404, detail="JD not found")
		final_text = body.get("final_text", model.final_text)
		title = body.get("title", model.title)
		notes = body.get("notes", model.notes)
		tags = body.get("tags", model.tags)
		updated = service.update_partial(db, jd_id, {"final_text": final_text, "title": title, "notes": notes, "tags": tags})
		return JDRead(
			id=updated.id,
			title=updated.title,
			role=updated.role,
			original_text=updated.original_text,
			refined_text=updated.refined_text,
			company_id=updated.company_id,
			notes=updated.notes,
			tags=updated.tags or [],
			final_text=updated.final_text,
		)
	except (ValueError, SQLAlchemyError) as e:
		if isinstance(e, SQLAlchemyError):
			rollback_on_error(db)
		raise handle_service_errors(e)
