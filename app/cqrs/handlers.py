from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.services.jd_service import JDService
from app.services.persona_service import PersonaService
from app.services.candidate_service import CandidateService
from app.services.match_service import MatchService


class Command:  # placeholder base
	pass


class Query:  # placeholder base
	pass


# Command classes
class CreateJobDescription(Command):
	def __init__(self, payload: dict):
		self.payload = payload


class ApplyJDRefinement(Command):
	def __init__(self, jd_id: str, refined_text: str):
		self.jd_id = jd_id
		self.refined_text = refined_text


class CreatePersona(Command):
	def __init__(self, payload: dict):
		self.payload = payload


class UploadCVs(Command):
	def __init__(self, payloads: list[dict]):
		self.payloads = payloads


class ScoreCandidates(Command):
	def __init__(self, candidate_ids: list[str], persona_id: str, persona_weights: dict, per_candidate_scores: dict):
		self.candidate_ids = candidate_ids
		self.persona_id = persona_id
		self.persona_weights = persona_weights
		self.per_candidate_scores = per_candidate_scores


# Query classes
class PrepareJDRefinementBrief(Query):
	def __init__(self, jd_id: str, required_sections: list[str], template_text: str | None = None):
		self.jd_id = jd_id
		self.required_sections = required_sections
		self.template_text = template_text


class Recommendations(Query):
	def __init__(self, persona_id: str, top_k: int = 10):
		self.persona_id = persona_id
		self.top_k = top_k


# Handlers

def handle_command(db: Session, command: Command) -> Any:
	if isinstance(command, CreateJobDescription):
		return JDService().create(db, command.payload)
	if isinstance(command, ApplyJDRefinement):
		return JDService().apply_refinement(db, command.jd_id, command.refined_text)
	if isinstance(command, CreatePersona):
		return PersonaService().create(db, command.payload)
	if isinstance(command, UploadCVs):
		return CandidateService().upload(db, command.payloads)
	if isinstance(command, ScoreCandidates):
		return CandidateService().score_candidates(
			db,
			command.candidate_ids,
			command.persona_id,
			command.persona_weights,
			command.per_candidate_scores,
		)
	raise NotImplementedError(f"No handler for command {type(command).__name__}")


def handle_query(db: Session, query: Query) -> Any:
	if isinstance(query, PrepareJDRefinementBrief):
		return JDService().prepare_refinement_brief(db, query.jd_id, query.required_sections, query.template_text)
	if isinstance(query, Recommendations):
		return MatchService().recommendations(db, query.persona_id, query.top_k)
	raise NotImplementedError(f"No handler for query {type(query).__name__}")
