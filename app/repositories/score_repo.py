from __future__ import annotations

from typing import List, Sequence
from sqlalchemy.orm import Session

from app.db.models.score import ScoreModel


class ScoreRepository:
	"""Repository interface for Score records."""

	def bulk_create(self, db: Session, scores: List[ScoreModel]) -> List[ScoreModel]:
		raise NotImplementedError

	def list_for_candidate_persona(self, db: Session, candidate_id: str, persona_id: str) -> Sequence[ScoreModel]:
		raise NotImplementedError


class SQLAlchemyScoreRepository(ScoreRepository):
	"""SQLAlchemy-backed implementation of ScoreRepository."""

	def bulk_create(self, db: Session, scores: List[ScoreModel]) -> List[ScoreModel]:
		if not scores:
			return []
		db.add_all(scores)
		db.commit()
		for s in scores:
			db.refresh(s)
		return scores

	def list_for_candidate_persona(self, db: Session, candidate_id: str, persona_id: str) -> Sequence[ScoreModel]:
		return (
			db.query(ScoreModel)
			.filter(ScoreModel.candidate_id == candidate_id, ScoreModel.persona_id == persona_id)
			.order_by(ScoreModel.category.asc())
			.all()
		)
