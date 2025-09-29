from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.services.jd_service import JDService
from app.services.persona_service import PersonaService
from app.services.candidate_service import CandidateService
from app.services.match_service import MatchService

# Import base classes
from app.cqrs.commands.base import Command
from app.cqrs.queries.base import Query

# Import command classes
from app.cqrs.commands.jd_commands import (
	CreateJobDescription,
	ApplyJDRefinement,
	UpdateJobDescription,
)
from app.cqrs.commands.upload_jd_document import UploadJobDescriptionDocument
from app.cqrs.commands.create_persona import CreatePersona
from app.cqrs.commands.upload_cv import UploadCVs
from app.cqrs.commands.score_candidates import ScoreCandidates

# Import query classes
from app.cqrs.queries.jd_queries import (
	ListJobDescriptions,
	GetJobDescription,
	PrepareJDRefinementBrief,
)
from app.cqrs.queries.get_persona import GetPersona
from app.cqrs.queries.list_candidates import ListCandidates
from app.cqrs.queries.recommendations import Recommendations


# Handlers

def handle_command(db: Session, command: Command) -> Any:
	if isinstance(command, CreateJobDescription):
		return JDService().create(db, command.payload)
	if isinstance(command, ApplyJDRefinement):
		return JDService().apply_refinement(db, command.jd_id, command.refined_text)
	if isinstance(command, UpdateJobDescription):
		return JDService().update_partial(db, command.jd_id, command.fields)
	if isinstance(command, UploadJobDescriptionDocument):
		return JDService().create_from_document(db, command.payload, command.file_content, command.filename)
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
	if isinstance(query, ListJobDescriptions):
		return JDService().list_by_creator(db, query.user_id)
	if isinstance(query, GetJobDescription):
		return JDService().get_by_id(db, query.jd_id)
	if isinstance(query, PrepareJDRefinementBrief):
		return JDService().prepare_refinement_brief(db, query.jd_id, query.required_sections, query.template_text)
	if isinstance(query, Recommendations):
		return MatchService().recommendations(db, query.persona_id, query.top_k)
	raise NotImplementedError(f"No handler for query {type(query).__name__}")
