from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.services.jd_service import JDService
from app.services.persona_service import PersonaService
from app.services.candidate_service import CandidateService
from app.services.match_service import MatchService
from app.services.company_service import CompanyService
from app.services.job_role_service import JobRoleService
from app.services.persona_level_service import PersonaLevelService
from app.cqrs.commands.generate_persona_from_jd import GeneratePersonaFromJD
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
from app.cqrs.commands.company_commands import (
    CreateCompany,
    UpdateCompany,
    DeleteCompany
)
from app.cqrs.commands.job_role_commands import (
    CreateJobRole,
    UpdateJobRole,
    DeleteJobRole
)
from app.cqrs.commands.create_persona import CreatePersona
from app.cqrs.commands.persona_level_commands import (
	CreatePersonaLevel,
	UpdatePersonaLevel,
	DeletePersonaLevel
)
from app.cqrs.commands.persona_commands import (
	CreatePersona,
	UpdatePersona,
	DeletePersona
)
from app.cqrs.commands.upload_cv import UploadCVs
from app.cqrs.commands.score_candidates import ScoreCandidates

# Import query classes
from app.cqrs.queries.jd_queries import (
	ListJobDescriptions,
	ListAllJobDescriptions,
	GetJobDescription,
	PrepareJDRefinementBrief,
)
from app.cqrs.queries.get_persona import GetPersona
from app.cqrs.queries.list_candidates import ListCandidates
from app.cqrs.queries.recommendations import Recommendations
from app.cqrs.queries.company_queries import (
    GetCompany,
    GetCompanyByName,
    ListCompanies,
    SearchCompanies,
    CountCompanies,
    CountSearchCompanies
)
from app.cqrs.queries.job_role_queries import (
    GetJobRole,
    GetJobRoleByName,
    ListJobRoles,
    ListActiveJobRoles,
    GetJobRolesByCategory,
    SearchJobRoles,
    CountJobRoles,
    CountActiveJobRoles,
    CountSearchJobRoles,
    GetJobRoleCategories
)
from app.cqrs.queries.persona_queries import (
	GetPersona,
	ListPersonasByJobDescription,
	ListAllPersonas,
	CountPersonas
)
from app.cqrs.queries.persona_level_queries import (
	GetPersonaLevel,
	GetPersonaLevelByName,
	ListPersonaLevels,
	ListAllPersonaLevels,
	GetPersonaLevelByPosition
)

import asyncio
import concurrent.futures
from app.cqrs.commands.refine_jd_with_ai import RefineJDWithAI
from app.cqrs.queries.jd_queries import GetJDDiff
from app.cqrs.queries.jd_queries import GetJDInlineMarkup
# Add this handler function before handle_command
def handle_refine_jd_with_ai(db: Session, command: RefineJDWithAI):
    """Handle JD refinement with AI (sync wrapper for async service)"""
    
    try:
        # Try to get running loop
        try:
            loop = asyncio.get_running_loop()
            # Loop exists (FastAPI context), use thread pool
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    JDService().apply_refinement_with_ai(
                        db=db,
                        jd_id=command.jd_id,
                        role=command.role,
                        company_id=command.company_id,
                        methodology=command.methodology,
                        min_similarity=command.min_similarity
                    )
                )
                return future.result()
        except RuntimeError:
            # No running loop, create and run
            return asyncio.run(
                JDService().apply_refinement_with_ai(
                    db=db,
                    jd_id=command.jd_id,
                    role=command.role,
                    company_id=command.company_id,
                    methodology=command.methodology,
                    min_similarity=command.min_similarity
                )
            )
    except Exception as e:
        raise ValueError(f"Error in AI refinement: {str(e)}")
	
def handle_generate_persona_from_jd(db: Session, command: GeneratePersonaFromJD):
    """Handle persona generation from JD (returns structure, doesn't save)"""
    try:
        # Get JD text
        jd = JDService().get_by_id(db, command.jd_id)
        if not jd:
            raise ValueError(f"Job description {command.jd_id} not found")
        
        jd_text = jd.refined_text or jd.original_text
        
        # Import here to avoid circular dependency
        from app.services.persona_generation import OpenAIPersonaGenerator
        from app.core.config import settings
        
        # Initialize generator
        generator = OpenAIPersonaGenerator(
            api_key=settings.OPENAI_API_KEY,
            model=getattr(settings, "PERSONA_GENERATION_MODEL", "gpt-4o")
        )
        
        # Run async persona generation (returns dict, doesn't save)
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    generator.generate_persona_from_jd(
                        jd_text=jd_text,
                        jd_id=command.jd_id
                    )
                )
                return future.result()
        except RuntimeError:
            return asyncio.run(
                generator.generate_persona_from_jd(
                    jd_text=jd_text,
                    jd_id=command.jd_id
                )
            )
    except Exception as e:
        raise ValueError(f"Error generating persona structure: {str(e)}")
# Handlers

def handle_command(db: Session, command: Command) -> Any:
	if isinstance(command, CreateJobDescription):
		return JDService().create(db, command.payload)
	if isinstance(command, ApplyJDRefinement):
		return JDService().apply_refinement(db, command.jd_id, command.refined_text)
	if isinstance(command, RefineJDWithAI):
		return handle_refine_jd_with_ai(db, command)
	if isinstance(command, UpdateJobDescription):
		return JDService().update_partial(db, command.jd_id, command.fields, command.updated_by)
	if isinstance(command, UploadJobDescriptionDocument):
		return JDService().create_from_document(db, command.payload, command.file_content, command.filename)
	if isinstance(command, CreatePersona):
		return PersonaService().create_nested(db, command.payload, command.created_by)
	if isinstance(command, GeneratePersonaFromJD):
		return handle_generate_persona_from_jd(db, command)
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
	if isinstance(command, CreateCompany):
		return CompanyService().create(db, command.payload)
	if isinstance(command, UpdateCompany):
		return CompanyService().update(db, command.company_id, command.payload)
	if isinstance(command, DeleteCompany):
		return CompanyService().delete(db, command.company_id)
	if isinstance(command, CreateJobRole):
		return JobRoleService().create(db, command.payload)
	if isinstance(command, UpdateJobRole):
		return JobRoleService().update(db, command.job_role_id, command.payload)
	if isinstance(command, DeleteJobRole):
		return JobRoleService().delete(db, command.job_role_id)
	if isinstance(command, CreatePersonaLevel):
		return PersonaLevelService().create_level(db, command.payload)
	if isinstance(command, UpdatePersonaLevel):
		return PersonaLevelService().update_level(db, command.persona_level_id, command.payload)
	if isinstance(command, DeletePersonaLevel):
		return PersonaLevelService().delete_level(db, command.persona_level_id)
	raise NotImplementedError(f"No handler for command {type(command).__name__}")


def handle_query(db: Session, query: Query) -> Any:
	if isinstance(query, ListJobDescriptions):
		return JDService().list_by_creator(db, query.user_id)
	if isinstance(query, ListAllJobDescriptions):
		return JDService().list_all(db)
	if isinstance(query, GetJobDescription):
		return JDService().get_by_id(db, query.jd_id)
	if isinstance(query, PrepareJDRefinementBrief):
		return JDService().prepare_refinement_brief(db, query.jd_id, query.required_sections, query.template_text)
	if isinstance(query, Recommendations):
		return MatchService().recommendations(db, query.persona_id, query.top_k)
	if isinstance(query, GetCompany):
		return CompanyService().get_by_id(db, query.company_id)
	if isinstance(query, GetCompanyByName):
		return CompanyService().get_by_name(db, query.name)
	if isinstance(query, ListCompanies):
		return CompanyService().get_all(db, query.skip, query.limit)
	if isinstance(query, SearchCompanies):
		return CompanyService().search(db, query.search_criteria, query.skip, query.limit)
	if isinstance(query, CountCompanies):
		return CompanyService().count(db)
	if isinstance(query, CountSearchCompanies):
		return CompanyService().count_search(db, query.search_criteria)
	if isinstance(query, GetJobRole):
		return JobRoleService().get_by_id(db, query.job_role_id)
	if isinstance(query, GetJobRoleByName):
		return JobRoleService().get_by_name(db, query.name)
	if isinstance(query, ListJobRoles):
		return JobRoleService().get_all(db, query.skip, query.limit)
	if isinstance(query, ListActiveJobRoles):
		return JobRoleService().get_active(db, query.skip, query.limit)
	if isinstance(query, GetJobRolesByCategory):
		return JobRoleService().get_by_category(db, query.category, query.skip, query.limit)
	if isinstance(query, SearchJobRoles):
		return JobRoleService().search(db, query.search_criteria, query.skip, query.limit)
	if isinstance(query, CountJobRoles):
		return JobRoleService().count(db)
	if isinstance(query, CountActiveJobRoles):
		return JobRoleService().count_active(db)
	if isinstance(query, CountSearchJobRoles):
		return JobRoleService().count_search(db, query.search_criteria)
	if isinstance(query, GetJobRoleCategories):
		return JobRoleService().get_categories(db)
	if isinstance(query, GetJDDiff):
		return JDService().get_jd_diff(db, query.jd_id, query.diff_format)
	if isinstance(query, GetJDInlineMarkup):
		return JDService().get_jd_inline_markup(db, query.jd_id)
	if isinstance(query, GetPersonaLevel):
		return PersonaLevelService().get_level(db, query.persona_level_id)
	if isinstance(query, GetPersonaLevelByName):
		return PersonaLevelService().get_level_by_name(db, query.name)
	if isinstance(query, ListPersonaLevels):
		return PersonaLevelService().list_levels(db, query.sort_by_position)
	if isinstance(query, ListAllPersonaLevels):
		return PersonaLevelService().get_levels_count(db)
	if isinstance(query, GetPersonaLevelByPosition):
		return PersonaLevelService().get_level_by_position(db, query.position)
	if isinstance(query, ListPersonasByJobDescription):
		return PersonaService().list_by_jd(db, query.job_description_id)
	if isinstance(query, ListAllPersonas):
		return PersonaService().list_all(db)
	if isinstance(query, CountPersonas):
		return PersonaService().count(db)
	if isinstance(query, GetPersona):
		return PersonaService().get_persona(db, query.persona_id)
	raise NotImplementedError(f"No handler for query {type(query).__name__}")
