from __future__ import annotations

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.repositories.score_repo import SQLAlchemyScoreRepository
from app.repositories.candidate_repo import SQLAlchemyCandidateRepository
from app.domain.candidate import rules as cand_rules


class MatchService:
	"""Handles scoring-related read operations and recommendations."""

	def __init__(self, scores: Optional[SQLAlchemyScoreRepository] = None, candidates: Optional[SQLAlchemyCandidateRepository] = None):
		self.scores = scores or SQLAlchemyScoreRepository()
		self.candidates = candidates or SQLAlchemyCandidateRepository()

	def recommendations(self, db: Session, persona_id: str, top_k: int = 10) -> List[dict]:
		"""Return a simple top-k list based on candidate stored total scores."""
		all_candidates = self.candidates.list_all(db)
		ranked = []
		for c in all_candidates:
			total = 0.0
			if c.scores and "__total__" in c.scores:
				total = float(c.scores["__total__"])
			ranked.append({"candidate_id": c.id, "name": c.name, "total": total, "band": cand_rules.band_fit(total)})
		ranked.sort(key=lambda x: x["total"], reverse=True)
		return ranked[: max(1, int(top_k))]
