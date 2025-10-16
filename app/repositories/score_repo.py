from __future__ import annotations

from typing import List, Sequence, Optional
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models.score import (
	CandidateScoreModel, ScoreStageModel, ScoreCategoryModel, 
	ScoreSubcategoryModel, ScoreInsightModel
)


class ScoreRepository:
	"""Repository interface for comprehensive scoring records."""

	def create_candidate_score(self, db: Session, score: CandidateScoreModel) -> CandidateScoreModel:
		raise NotImplementedError

	def get_candidate_score(self, db: Session, score_id: str) -> Optional[CandidateScoreModel]:
		raise NotImplementedError

	def list_scores_for_candidate_persona(self, db: Session, candidate_id: str, persona_id: str) -> Sequence[CandidateScoreModel]:
		raise NotImplementedError

	def list_scores_for_cv_persona(self, db: Session, cv_id: str, persona_id: str) -> Sequence[CandidateScoreModel]:
		raise NotImplementedError

	def list_candidate_scores(self, db: Session, candidate_id: str, skip: int = 0, limit: int = 100) -> Sequence[CandidateScoreModel]:
		raise NotImplementedError

	def list_all_scores(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[CandidateScoreModel]:
		raise NotImplementedError


class SQLAlchemyScoreRepository(ScoreRepository):
	"""SQLAlchemy-backed implementation of comprehensive ScoreRepository."""

	def create_candidate_score(self, db: Session, score: CandidateScoreModel) -> CandidateScoreModel:
		db.add(score)
		db.commit()
		db.refresh(score)
		return score

	def get_candidate_score(self, db: Session, score_id: str) -> Optional[CandidateScoreModel]:
		return (
			db.query(CandidateScoreModel)
			.options(
				selectinload(CandidateScoreModel.score_stages),
				selectinload(CandidateScoreModel.categories).selectinload(ScoreCategoryModel.subcategories),
				selectinload(CandidateScoreModel.insights)
			)
			.filter(CandidateScoreModel.id == score_id)
			.first()
		)

	def list_scores_for_candidate_persona(self, db: Session, candidate_id: str, persona_id: str) -> Sequence[CandidateScoreModel]:
		return (
			db.query(CandidateScoreModel)
			.options(
				selectinload(CandidateScoreModel.score_stages),
				selectinload(CandidateScoreModel.categories).selectinload(ScoreCategoryModel.subcategories),
				selectinload(CandidateScoreModel.insights)
			)
			.filter(
				CandidateScoreModel.candidate_id == candidate_id, 
				CandidateScoreModel.persona_id == persona_id
			)
			.order_by(CandidateScoreModel.scored_at.desc())
			.all()
		)

	def list_scores_for_cv_persona(self, db: Session, cv_id: str, persona_id: str) -> Sequence[CandidateScoreModel]:
		return (
			db.query(CandidateScoreModel)
			.options(
				selectinload(CandidateScoreModel.score_stages),
				selectinload(CandidateScoreModel.categories).selectinload(ScoreCategoryModel.subcategories),
				selectinload(CandidateScoreModel.insights)
			)
			.filter(
				CandidateScoreModel.cv_id == cv_id, 
				CandidateScoreModel.persona_id == persona_id
			)
			.order_by(CandidateScoreModel.scored_at.desc())
			.all()
		)

	def list_candidate_scores(self, db: Session, candidate_id: str, skip: int = 0, limit: int = 100) -> Sequence[CandidateScoreModel]:
		return (
			db.query(CandidateScoreModel)
			.options(
				selectinload(CandidateScoreModel.score_stages),
				selectinload(CandidateScoreModel.categories).selectinload(ScoreCategoryModel.subcategories),
				selectinload(CandidateScoreModel.insights)
			)
			.filter(CandidateScoreModel.candidate_id == candidate_id)
			.order_by(CandidateScoreModel.scored_at.desc())
			.offset(skip)
			.limit(limit)
			.all()
		)

	def list_all_scores(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[CandidateScoreModel]:
		return (
			db.query(CandidateScoreModel)
			.options(
				selectinload(CandidateScoreModel.score_stages),
				selectinload(CandidateScoreModel.categories).selectinload(ScoreCategoryModel.subcategories),
				selectinload(CandidateScoreModel.insights)
			)
			.order_by(CandidateScoreModel.scored_at.desc())
			.offset(skip)
			.limit(limit)
			.all()
		)
