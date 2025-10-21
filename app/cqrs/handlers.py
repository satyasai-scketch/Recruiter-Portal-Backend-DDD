from __future__ import annotations

from typing import Any, Dict
from sqlalchemy.orm import Session

from app.services.jd_service import JDService
from app.services.persona_service import PersonaService
from app.services.candidate_service import CandidateService
from app.services.match_service import MatchService
from app.services.company_service import CompanyService
from app.services.job_role_service import JobRoleService
from app.services.persona_level_service import PersonaLevelService
from app.services.user_service import UserService
from app.cqrs.commands.generate_persona_from_jd import GeneratePersonaFromJD
from app.cqrs.commands.score_with_ai import ScoreCandidateWithAI
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
from app.cqrs.commands.upload_cv_file import UploadCVFile
from app.cqrs.commands.candidate_commands import UpdateCandidate, UpdateCandidateCV, DeleteCandidate, DeleteCandidateCV
from app.cqrs.commands.score_candidates import ScoreCandidate
from app.cqrs.commands.user_commands import UpdateUser

# Import query classes
from app.cqrs.queries.jd_queries import (
	ListJobDescriptions,
	ListAllJobDescriptions,
	GetJobDescription,
	PrepareJDRefinementBrief,
)
from app.cqrs.queries.get_persona import GetPersona
from app.cqrs.queries.list_candidates import ListCandidates
from app.cqrs.queries.candidate_queries import (
	GetCandidate,
	ListAllCandidates,
	GetCandidateCV,
	GetCandidateCVs
)
from app.cqrs.queries.score_queries import (
	GetCandidateScore,
	ListCandidateScores,
	ListScoresForCandidatePersona,
	ListScoresForCVPersona,
	ListLatestCandidateScoresPerPersona,
	ListAllScores
)
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
	CountPersonas,
	GetPersonaChangeLogs,
	ListPersonasByJobRole
)
from app.cqrs.queries.persona_level_queries import (
	GetPersonaLevel,
	GetPersonaLevelByName,
	ListPersonaLevels,
	ListAllPersonaLevels,
	GetPersonaLevelByPosition
)
from app.cqrs.queries.user_queries import (
	ListAllUsers,
	GetUser
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

def normalize_ai_scoring_response(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize AI scoring response to always have consistent structure,
    regardless of which pipeline stage it terminated at.
    
    This ensures score_candidate method always gets the expected data structure.
    Handles early rejection (Stage 1/2) by providing empty Stage 3 structures.
    """
    normalized = {
        'pipeline_stage_reached': ai_response.get('pipeline_stage_reached', 1),
        'final_score': ai_response.get('final_score', 0.0),
        'final_decision': ai_response.get('final_decision', 'UNKNOWN'),
        'score_progression': ai_response.get('score_progression') or {},
    }
    
    stage_reached = normalized['pipeline_stage_reached']
    
    # ========== STAGE 1 DATA ==========
    # Always present
    normalized['stage1'] = ai_response.get('stage1') or {
        'method': 'embedding',
        'model': 'text-embedding-3-small',
        'score': 0.0,
        'threshold': 60.0,
        'decision': 'UNKNOWN',
        'reason': 'No stage 1 data available'
    }
    
    # ========== STAGE 2 DATA ==========
    # Present only if stage reached >= 2
    if stage_reached >= 2:
        normalized['stage2'] = ai_response.get('stage2') or {
            'method': 'lightweight_llm',
            'model': 'gpt-4o-mini',
            'relevance_score': 0,
            'threshold': 60,
            'decision': 'UNKNOWN',
            'reason': 'No stage 2 data available',
            'skills': [],
            'roles_detected': [],
            'quick_assessment': ''
        }
    else:
        normalized['stage2'] = None
    
    # ========== STAGE 3 DATA ==========
    # This is the critical part - must have structure even if not reached
    if stage_reached >= 3:
        # Stage 3 was reached - use actual data
        stage3_data = ai_response.get('stage3') or {}
        
        normalized['stage3'] = {
            'method': 'detailed_llm',
            'model': 'gpt-4o',
            'overall_score': stage3_data.get('overall_score', 0.0),
            'categories': stage3_data.get('categories', []),
            'strengths': stage3_data.get('strengths', []),
            'gaps': stage3_data.get('gaps', []),
            'recommendation': stage3_data.get('recommendation', 'UNKNOWN'),
            'reasoning': stage3_data.get('reasoning', '')
        }
    else:
        # Stage 3 NOT reached (rejected at Stage 1 or 2)
        # Provide empty structure so score_candidate doesn't crash
        normalized['stage3'] = {
            'method': 'detailed_llm',
            'model': 'gpt-4o',
            'overall_score': 0.0,
            'categories': [],  # Empty list prevents iteration errors
            'strengths': [],   # Empty list prevents iteration errors
            'gaps': [],        # Empty list prevents iteration errors
            'recommendation': 'REJECTED',
            'reasoning': f"Rejected at stage {stage_reached}"
        }
    
    return normalized


# Add this to your handlers.py
def handle_score_candidate_with_ai(db: Session, command: ScoreCandidateWithAI):
    """Handle AI-powered CV scoring"""
    import asyncio
    import concurrent.futures
    
    try:
        # Get CV text
        cv = CandidateService().candidate_cvs.get(db, command.cv_id)
        if not cv:
            raise ValueError(f"CV {command.cv_id} not found")
        
        cv_text = cv.cv_text
        if not cv_text:
            raise ValueError(f"CV {command.cv_id} has no extracted text")
        
        # Get persona
        from app.services.persona_service import PersonaService
        persona_model = PersonaService().get_persona(db, command.persona_id)
        if not persona_model:
            raise ValueError(f"Persona {command.persona_id} not found")
        
        # Convert persona to dict
        persona_dict = _persona_to_dict(persona_model)
        
        # Run async AI scoring
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    CandidateService().score_candidate_with_ai(
                        cv_text=cv_text,
                        persona_dict=persona_dict
                    )
                )
                raw_response = future.result()
        except RuntimeError:
            raw_response = asyncio.run(
                CandidateService().score_candidate_with_ai(
                    cv_text=cv_text,
                    persona_dict=persona_dict
                )
            )
        
        # ⭐ NORMALIZE RESPONSE - Ensures consistent structure for score_candidate
        normalized_response = normalize_ai_scoring_response(raw_response)
        
        return normalized_response
        
    except Exception as e:
        raise ValueError(f"Error scoring candidate with AI: {str(e)}")


def _persona_to_dict(persona_model):
    """Convert PersonaModel to dict for AI scoring"""
    categories = []
    
    for cat in persona_model.categories:
        subcategories = []
        
        for sub in cat.subcategories:
            subcat_dict = {
                'name': sub.name,
                'weight_percentage': sub.weight_percentage,
                'range_min': sub.range_min,
                'range_max': sub.range_max,
                'level_id': str(sub.level.position) if sub.level_id else '3',
                'position': sub.position
            }
            
            if sub.skillset:
                subcat_dict['skillset'] = {
                    'technologies': sub.skillset.technologies or []
                }
            
            subcategories.append(subcat_dict)
        
        cat_dict = {
            'name': cat.name,
            'weight_percentage': cat.weight_percentage,
            'range_min': cat.range_min,
            'range_max': cat.range_max,
            'position': cat.position,
            'subcategories': subcategories
        }
        
        if cat.notes:
            cat_dict['notes'] = {
                'custom_notes': cat.notes.custom_notes or ''
            }
        
        categories.append(cat_dict)
    
    return {
        'job_description_id': persona_model.job_description_id,
        'name': persona_model.name,
        'categories': categories
    }
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
	if isinstance(command, ScoreCandidateWithAI):
		return handle_score_candidate_with_ai(db, command)
	if isinstance(command, UpdatePersona):
		return PersonaService().update_persona(db, command.persona_id, command.payload, command.updated_by)
	if isinstance(command, DeletePersona):
		return PersonaService().delete_persona(db, command.persona_id)

	if isinstance(command, UploadCVs):
		return CandidateService().upload(db, command.payloads)
	if isinstance(command, UploadCVFile):
		return CandidateService().upload_cv(db, command.file_bytes, command.filename, command.candidate_info)
	if isinstance(command, ScoreCandidate):
		return CandidateService().score_candidate(
			db,
			command.candidate_id,
			command.persona_id,
			command.cv_id,
			command.ai_scoring_response,
			command.scoring_version,
			command.processing_time_ms,
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
	if isinstance(command, UpdateCandidate):
		return CandidateService().update_candidate(db, command.candidate_id, command.update_data)
	if isinstance(command, UpdateCandidateCV):
		return CandidateService().update_candidate_cv(db, command.cv_id, command.update_data)
	if isinstance(command, DeleteCandidate):
		return CandidateService().delete_candidate(db, command.candidate_id)
	if isinstance(command, DeleteCandidateCV):
		return CandidateService().delete_candidate_cv(db, command.candidate_cv_id)
	if isinstance(command, UpdateUser):
		return UserService().update(db, command.user_id, command.payload)
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
	if isinstance(query, GetPersonaChangeLogs):
		return PersonaService().get_change_logs(db, query.persona_id)
	if isinstance(query, ListPersonasByJobRole):
		return PersonaService().list_by_role_id(db, query.role_id)
	if isinstance(query, GetCandidate):
		return CandidateService().get_by_id(db, query.candidate_id)
	if isinstance(query, ListAllCandidates):
		return CandidateService().get_all(db, query.skip, query.limit)
	if isinstance(query, GetCandidateCV):
		return CandidateService().get_candidate_cv(db, query.candidate_cv_id)
	if isinstance(query, GetCandidateCVs):
		return CandidateService().get_candidate_cvs(db, query.candidate_id)
	if isinstance(query, GetCandidateScore):
		return CandidateService().get_candidate_score(db, query.score_id)
	if isinstance(query, ListCandidateScores):
		return CandidateService().list_candidate_scores(db, query.candidate_id, query.skip, query.limit)
	if isinstance(query, ListScoresForCandidatePersona):
		return CandidateService().list_scores_for_candidate_persona(db, query.candidate_id, query.persona_id, query.skip, query.limit)
	if isinstance(query, ListScoresForCVPersona):
		return CandidateService().list_scores_for_cv_persona(db, query.cv_id, query.persona_id, query.skip, query.limit)
	if isinstance(query, ListLatestCandidateScoresPerPersona):
		return CandidateService().list_latest_candidate_scores_per_persona(db, query.candidate_id, query.skip, query.limit)
	if isinstance(query, ListAllScores):
		return CandidateService().list_all_scores(db, query.skip, query.limit)
	if isinstance(query, ListAllUsers):
		return UserService().get_all(db, query.skip, query.limit)
	if isinstance(query, GetUser):
		return UserService().get_by_id(db, query.user_id)
	raise NotImplementedError(f"No handler for query {type(query).__name__}")
