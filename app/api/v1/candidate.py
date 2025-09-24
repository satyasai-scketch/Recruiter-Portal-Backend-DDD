from typing import List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.candidate import CandidateCreate, CandidateRead
from app.cqrs.handlers import UploadCVs, ScoreCandidates, handle_command

router = APIRouter()


@router.post("/upload", response_model=List[CandidateRead], summary="Upload candidate CVs (command)")
async def upload_cvs(payloads: List[CandidateCreate], db: Session = Depends(db_session)):
	models = handle_command(db, UploadCVs([p.dict() for p in payloads]))
	return [
		CandidateRead(
			id=m.id,
			name=m.name,
			email=m.email,
			phone=m.phone,
			years_experience=m.years_experience,
			skills=m.skills or [],
			education=m.education,
			cv_path=m.cv_path,
			summary=m.summary,
			scores=m.scores,
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
