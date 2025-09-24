from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.jd import JDCreate, JDRead
from app.cqrs.handlers import (
	CreateJobDescription,
	ApplyJDRefinement,
	PrepareJDRefinementBrief,
	handle_command,
	handle_query,
)

router = APIRouter()


@router.post("/", response_model=JDRead, summary="Create job description (command)")
async def create_jd(payload: JDCreate, db: Session = Depends(db_session)):
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
	)


class JDRefinementRequest(JDCreate):
	refined_text: str


@router.post("/{jd_id}/refine", summary="Apply refined JD (command)")
async def refine_jd(jd_id: str, body: dict, db: Session = Depends(db_session)):
	refined_text = body.get("refined_text")
	if not refined_text:
		raise HTTPException(status_code=400, detail="'refined_text' is required")
	model = handle_command(db, ApplyJDRefinement(jd_id, refined_text))
	return {"id": model.id, "refined_text": model.refined_text}


@router.get("/{jd_id}/refinement-brief", summary="Prepare refinement brief (query)")
async def refinement_brief(jd_id: str, db: Session = Depends(db_session)):
	brief = handle_query(
		db,
		PrepareJDRefinementBrief(
			jd_id,
			required_sections=["Responsibilities", "Requirements", "Benefits"],
			template_text=None,
		),
	)
	return brief
