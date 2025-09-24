from __future__ import annotations

from typing import Optional, Iterable, Dict, List
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.candidate import CandidateModel
from app.db.models.score import ScoreModel
from app.repositories.candidate_repo import SQLAlchemyCandidateRepository
from app.repositories.score_repo import SQLAlchemyScoreRepository
from app.domain.candidate import services as cand_domain_services
from app.events.event_bus import event_bus
from app.events.candidate_events import CVUploadedEvent, ScoreRequestedEvent


class CandidateService:
	"""Orchestrates candidate workflows at the application layer."""

	def __init__(
		self,
		candidates: Optional[SQLAlchemyCandidateRepository] = None,
		scores: Optional[SQLAlchemyScoreRepository] = None,
	):
		self.candidates = candidates or SQLAlchemyCandidateRepository()
		self.scores = scores or SQLAlchemyScoreRepository()

	def upload(self, db: Session, payloads: Iterable[dict]) -> List[CandidateModel]:
		"""Create candidates from payloads using domain validation."""
		created: List[CandidateModel] = []
		for data in (payloads or []):
			cand_agg = cand_domain_services.create_candidate(
				id=str(uuid4()),
				name=data["name"],
				email=data.get("email"),
				phone=data.get("phone"),
				years_experience=data.get("years_experience"),
				skills=data.get("skills") or [],
				education=data.get("education"),
				cv_path=data.get("cv_path"),
				summary=data.get("summary"),
			)
			model = CandidateModel(
				id=cand_agg.id,
				name=cand_agg.name,
				email=cand_agg.email,
				phone=cand_agg.phone,
				years_experience=cand_agg.years_experience,
				skills=cand_agg.skills,
				education=cand_agg.education,
				cv_path=cand_agg.cv_path,
				summary=cand_agg.summary,
				scores=cand_agg.scores,
			)
			created.append(self.candidates.create(db, model))
		# Publish a batch event with created candidate IDs
		event_bus.publish_event(CVUploadedEvent(candidate_ids=[c.id for c in created]))
		return created

	def score_candidates(
		self,
		db: Session,
		candidate_ids: List[str],
		persona_id: str,
		persona_weights: Dict[str, float],
		per_candidate_category_scores: Dict[str, Dict[str, float]],
	) -> List[ScoreModel]:
		"""Persist per-category scores and return created score rows."""
		# Publish score requested event (async workers may pick up for deeper analysis)
		event_bus.publish_event(ScoreRequestedEvent(candidate_ids=candidate_ids, persona_id=persona_id, persona_weights=persona_weights))

		rows: List[ScoreModel] = []
		for cid in candidate_ids:
			category_scores = per_candidate_category_scores.get(cid, {})
			candidate = self.candidates.get(db, cid)
			if not candidate:
				continue
			updated = cand_domain_services.score_against_persona(
				candidate,
				persona_weights,
				category_scores,
			)
			candidate.scores = updated.scores
			self.candidates.update(db, candidate)

			for category, score in (category_scores or {}).items():
				rows.append(
					ScoreModel(
						id=str(uuid4()),
						candidate_id=cid,
						persona_id=persona_id,
						category=category,
						score=float(score),
					)
				)
		return self.scores.bulk_create(db, rows)
