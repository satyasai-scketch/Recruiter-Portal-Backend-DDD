from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.cqrs.handlers import Recommendations, handle_query

router = APIRouter()


@router.post("/score", summary="Score candidates (command)")
async def score_candidates():
	return {"message": "stub: score_candidates"}


@router.get("/recommendations", summary="Top recommendations (query)")
async def recommendations(persona_id: str, top_k: int = 10, db: Session = Depends(db_session)):
	return handle_query(db, Recommendations(persona_id, top_k))
